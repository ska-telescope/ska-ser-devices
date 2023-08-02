r"""
This module provides an application-layer client and server.

That is, a client server that works with application payloads rather
than at the bytestring level.
"""

import logging
from contextlib import contextmanager
from typing import (
    Callable,
    Generic,
    Iterator,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    overload,
)

RequestPayloadT = TypeVar("RequestPayloadT")
ResponsePayloadT = TypeVar("ResponsePayloadT")

logger = logging.getLogger(__name__)


# pylint: disable-next=too-few-public-methods
class TransportClientProtocol(Protocol):
    """
    Structural subtyping protocol for supported transport protocols.

    That is, in order for a transport protocol client to be supported by
    this module, it must provide a request method that is implemented
    to:

    * enter a session context with the server,
    * issue the client request,
    * return an iterator, for use by the application layer
      to read as many bytestrings as necessary in order
      to construct the complete response payload.
    * exit the session context.
    """

    @contextmanager
    def request(self, request: bytes) -> Iterator[Iterator[bytes]]:
        """
        Transact a client request.

        Enter a session context with the server, issue the request,
        and return an iterator for use by the application layer
        to read as many bytestrings as necessary
        to construct the complete response payload.

        :param request: the request bytes

        :yield: a bytes iterator by which to construct the response
        """  # noqa: DAR302


# pylint: disable-next=too-few-public-methods
class ApplicationServer(Generic[RequestPayloadT, ResponsePayloadT]):
    """
    A server of application payloads.

    It uses an underlying transport-layer server (such as a TCP server),
    but requests are unmarshalled into application-layer payloads
    before being delivered to the application-layer server backend.
    Responses from the server backend are application-layer payloads
    that this server marshals down to a bytestring
    and returns to the client.
    Thus, the server backend deals only in application payloads,
    and does not know any details about
    how the transport layer transmits those payloads.
    """

    def __init__(
        self,
        request_unmarshaller: Callable[[Iterator[bytes]], RequestPayloadT],
        response_marshaller: Callable[[ResponsePayloadT], bytes],
        callback: Callable[[RequestPayloadT], Optional[ResponsePayloadT]],
    ) -> None:
        """
        Initialise a new instance.

        :param request_unmarshaller: a callable that unmarshalls byte
            into application-layer request payloads.
        :param response_marshaller: a callable that marshalls
            application-layer response payloads into bytes
        :param callback: callback to the application layer.
            When this server receives a request payload,
            it calls the application layer with the request,
            and expects to receive a response payload back.
        """
        self._payload_callback = callback
        self._unmarshaller = request_unmarshaller
        self._marshaller = response_marshaller

    def __call__(self, bytes_iterator: Iterator[bytes]) -> Optional[bytes]:
        """
        Handle receipt of bytes from the transport layer.

        When the transport layer server receives some bytes,
        it calls this callback with a bytestring iterator.
        This callback uses that iterator to ingest bytestrings
        until it has enough bytes to unmarshall them
        into a complete application payload.
        The payload is passed to the server backend.
        Once this callback receives a response from the backend,
        it marshalls that response down to a bytestring,
        and returns it to the transport-layer server
        for returning to the client.

        :param bytes_iterator: a bytestring iterator.

        :return: the bytes to be returned to the client.
        """
        request_payload = self._unmarshaller(bytes_iterator)
        logger.info("Request %s", request_payload.decode("ascii"))
        response_payload = self._payload_callback(request_payload)
        if response_payload is None:
            return None
        return self._marshaller(response_payload)


# pylint: disable-next=too-few-public-methods
class ApplicationClient(Generic[RequestPayloadT, ResponsePayloadT]):
    """
    An application-layer client.

    It uses an underlying transport-layer client (such as a TCP client),
    but requests are application payloads rather than bytestrings.
    These must be marshalled into bytestrings
    before sending to the server.
    When a response is received from the server,
    the received bytes are unmarshalled into an application payload
    which is returned to the caller.
    Thus, the caller deals only in application payloads,
    and does not know any details about
    how the transport layer transmits those payloads,
    """

    def __init__(
        self,
        bytes_client: TransportClientProtocol,
        request_marshaller: Callable[[RequestPayloadT], bytes],
        response_unmarshaller: Callable[[Iterator[bytes]], ResponsePayloadT],
    ) -> None:
        """
        Initialise a new instance.

        :param bytes_client: the bytes-level client to use.
        :param request_marshaller: a callable that marshalls
            application-layer request payloads into bytes.
        :param response_unmarshaller: a callable that unmarshalls byte
            into application-layer response payloads.
        """
        self._bytes_client = bytes_client
        self._marshaller = request_marshaller
        self._unmarshaller = response_unmarshaller

    @overload  # for the type checker
    def __call__(self, request: RequestPayloadT) -> ResponsePayloadT:  # noqa: D102
        ...

    @overload  # for the type checker
    def __call__(  # noqa: D102
        self, request: RequestPayloadT, expect_response: Literal[True]
    ) -> ResponsePayloadT:
        ...

    @overload  # for the type checker
    def __call__(  # noqa: D102
        self, request: RequestPayloadT, expect_response: Literal[False]
    ) -> None:
        ...

    def __call__(
        self,
        request: RequestPayloadT,
        expect_response: bool = True,
    ) -> Optional[ResponsePayloadT]:
        """
        Call the client with a request.

        The client marshalls the request (an application payload)
        down to a bytestring,
        then hands the bytestring down to the bytestring TCP client
        for sending to the server.
        Upon receive of a bytestring response,
        this client unmarshalls it into an application payload,
        which is returned to the caller.

        :param request: the payload to be sent to the server
        :param expect_response: whether to wait for a response from the
            server. Defaults to True. In the unusual case where the
            client does not expect a response to their request, set this
            to False.

        :returns: a response payload
        """
        request_bytes = self._marshaller(request)
        logger.info("Request %s", request_bytes.decode("ascii").rstrip())
        with self._bytes_client.request(request_bytes) as bytes_iterator:
            if expect_response:
                return self._unmarshaller(bytes_iterator)
        return None
