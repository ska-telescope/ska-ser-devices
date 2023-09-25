r"""
This module provides an application-layer client and server.

That is, a client server that works with application payloads rather
than at the bytestring level.
"""
from __future__ import annotations

from types import TracebackType
from typing import Callable, Generic, Iterator, Protocol, Type, TypeVar

RequestPayloadT = TypeVar("RequestPayloadT")
ResponsePayloadT = TypeVar("ResponsePayloadT")


class TransportClientProtocol(Protocol):
    """
    Structural subtyping protocol for supported transport client.

    In order for a transport client to be supported by this module,
    it must provide a connect method that establishes a session,
    and also implement a session context manager.
    """

    def connect(self) -> TransportClientSessionProtocol:
        """
        Establish a connection, and return access to the session.

        :return: access to the session context.
        """  # noqa: DAR202

    def __enter__(self) -> TransportClientSessionProtocol:
        """
        Establish a connection, and enter a session context.

        :return: access to the session context.
        """  # noqa: DAR202

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exception: BaseException | None,
        trace: TracebackType | None,
    ) -> bool:
        """
        Close the session and exit the session context.

        :param exc_type: the type of exception thrown in the with block
        :param exception: the exception thrown in the with block
        :param trace: a traceback

        :returns: whether the exception (if any) has been fully handled
            by this method and should be swallowed i.e. not re-raised
        """  # noqa: DAR202


class TransportClientSessionProtocol(Protocol):
    """
    Structural subtyping protocol for supported transport client session.

    In order for a transport session to be supported by this module,
    it must provide a request method that is implemented to

    1. issue the client request, and
    2. return an iterator, for use by the application layer
       to read as many bytestrings as necessary in order
       to construct the complete response payload.
    """

    def request(self, request: bytes) -> Iterator[bytes]:
        """
        Transact a client request.

        Issue the request,
        and return an iterator for use by the application layer
        to read as many bytestrings as necessary
        to construct the complete response payload.

        :param request: the request bytes

        :yield: a bytes iterator by which to construct the response
        """  # noqa: DAR302

    def close(self) -> None:
        """Close the connection."""


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
        callback: Callable[[RequestPayloadT], ResponsePayloadT | None],
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

    def __call__(self, bytes_iterator: Iterator[bytes]) -> bytes | None:
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
        response_payload = self._payload_callback(request_payload)
        if response_payload is None:
            return None
        return self._marshaller(response_payload)


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
        self._request_marshaller = request_marshaller
        self._response_unmarshaller = response_unmarshaller

        self._session: ApplicationClientSession[
            RequestPayloadT, ResponsePayloadT
        ] | None = None

    def connect(self) -> ApplicationClientSession[RequestPayloadT, ResponsePayloadT]:
        """
        Establish a new connection.

        :return: access to the new session.
        """
        self._session = ApplicationClientSession[RequestPayloadT, ResponsePayloadT](
            self._request_marshaller,
            self._response_unmarshaller,
            self._bytes_client.connect(),
        )
        return self._session

    def __enter__(self) -> ApplicationClientSession[RequestPayloadT, ResponsePayloadT]:
        """
        Establish a new connection, and enter the new session context.

        :return: access to the session context.
        """
        return self.connect()

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exception: BaseException | None,
        trace: TracebackType | None,
    ) -> bool:
        """
        Exit method for "with" context.

        :param exc_type: the type of exception thrown in the with block
        :param exception: the exception thrown in the with block
        :param trace: a traceback
        :returns: whether the exception (if any) has been fully handled
            by this method and should be swallowed i.e. not re-raised
        """
        if self._session is not None:
            self._session.close()
            self._session = None
        return exception is None


class ApplicationClientSession(Generic[RequestPayloadT, ResponsePayloadT]):
    """A class for representing and managing a session."""

    def __init__(
        self,
        request_marshaller: Callable[[RequestPayloadT], bytes],
        response_unmarshaller: Callable[[Iterator[bytes]], ResponsePayloadT],
        transport_session: TransportClientSessionProtocol,
    ) -> None:
        """
        Initialise a new session instance.

        :param request_marshaller: a callable that marshalls
            application-layer request payloads into bytes.
        :param response_unmarshaller: a callable that unmarshalls byte
            into application-layer response payloads.
        :param transport_session: the underlying transport-layer session.
        """
        self._request_marshaller = request_marshaller
        self._response_unmarshaller = response_unmarshaller
        self._transport_session = transport_session

    def send(
        self,
        request: RequestPayloadT,
    ) -> None:
        """
        Call the client with a request, for which no response is expected.

        The client marshalls the request (an application payload)
        down to a bytestring,
        then hands the bytestring down to the bytestring TCP client
        for sending to the server.

        :param request: the payload to be sent to the server
        """
        request_bytes = self._request_marshaller(request)
        self._transport_session.request(request_bytes)

    def send_receive(
        self,
        request: RequestPayloadT,
    ) -> ResponsePayloadT:
        """
        Call the client with a request, for which a response is expected.

        The client marshalls the request (an application payload)
        down to a bytestring,
        then hands the bytestring down to the bytestring TCP client
        for sending to the server.
        Upon receive of a bytestring response,
        this client unmarshalls it into an application payload,
        which is returned to the caller.

        :param request: the payload to be sent to the server

        :returns: a response payload
        """
        request_bytes = self._request_marshaller(request)
        bytes_iterator = self._transport_session.request(request_bytes)
        return self._response_unmarshaller(bytes_iterator)

    def close(self) -> None:
        """Close the connection and end the session."""
        self._transport_session.close()
