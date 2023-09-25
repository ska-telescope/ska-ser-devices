r"""This module provides a Telnet client."""
from __future__ import annotations

import logging
from telnetlib import Telnet
from types import TracebackType
from typing import Iterator, Type

_module_logger = logging.getLogger(__name__)


class _TelnetBytestringIterator:
    """An iterator on Telnet byte buffers."""

    def __init__(
        self,
        session: Telnet,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise a new instance.

        :param session: the Telnet session
        :param logger: a python standard logger
        """
        self._session = session
        self._logger = logger or _module_logger

    def __iter__(self) -> Iterator[bytes]:
        """
        Return the iterator itself.

        :return: the iterator itself.
        """
        return self

    def __next__(self) -> bytes:
        """
        Return the next bytestring.

        :return: the next bytestring.

        :raises StopIteration: if the session performs an empty read.
        """
        bytestring = self._session.read_some()
        if not bytestring:
            self._logger.debug("Telnet session received no bytes.")
            raise StopIteration()  # not essential but helpful for debugging

        self._logger.debug(
            f"Telnet session received bytes {bytestring.hex()} "
            f"(raw string {repr(bytestring)})"
        )
        return bytestring


class TelnetClient:
    """
    A Telnet client.

    It handles client requests by sending the request bytes
    straight off to the server.
    However, when it receives a response,
    it creates a bytestring iterator
    and hands it up to the application layer,
    so that the application layer can receive as many bytestrings
    as it needs to constitute an application payload.
    """

    def __init__(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise a new instance.

        :param address: tuple consisting of the host name or IP address,
            and the port, of the server.
        :param timeout: how long to wait when attempting to send or
            receive data.
        :param logger: a python standard logger
        """
        self._address = address
        self._timeout = timeout
        self._logger = logger or _module_logger

        self._session: TelnetClientSession | None = None

    def connect(self) -> TelnetClientSession:
        """
        Establish a new connection.

        :return: access to the established session.
        """
        self._session = TelnetClientSession(self._address, self._timeout, self._logger)
        return self._session

    def __enter__(self) -> TelnetClientSession:
        """
        Establish a new connection and enter the session context.

        :return: access to the session context
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


class TelnetClientSession:
    """A class for representing and managing a TCP session."""

    def __init__(
        self,
        address: tuple[str, int],
        timeout: float | None,
        logger: logging.Logger,
    ) -> None:
        """
        Establish a new session.

        :param address: a tuple consisting of
            the host name or IP address,
            and the port, of the server.
        :param timeout: how long to wait when attempting to send or
            receive data, in seconds. If None, the socket blocks
            indefinitely.
        :param logger: a python standard logger
        """
        self._logger = logger

        # Oh, this is nasty.
        if timeout is None:
            self._telnet_session = Telnet(*address)
        else:
            self._telnet_session = Telnet(*address, timeout)

    def request(self, request: bytes) -> Iterator[bytes]:
        r"""
        Initiate a new client request.

        Call this method like

        .. code-block:: python

            with telnet_client as session:
                byte_iterator = session.request(request_bytes):
                response_bytes = next(bytes_iterator)
                if not response_bytes.endswith(b"\r\n"):
                    response_bytes += next(bytes_iterator)

        That is,

        * First enter into a session with the Telnet server
        * Then send the request data.
        * Since only the calling application can know
            when it has received enough bytes for a complete response,
            the session context returns a bytestring iterator
            for the application layer to use to retrieve blocks of bytes.
            (In this example, the application layer knows
            that the response is terminated by "\r\n",
            so it keeps receiving data until it encounters that sequence
            and the end of a block.)
        * Upon exiting the session context, the session is closed.

        :param request: request bytes.

        :returns: a bytestring iterator.
        """
        self._logger.debug(
            f"Telnet session sending request bytes {request.hex()} "
            f"(raw string {repr(request)})"
        )
        banner = self._telnet_session.read_some()  # read and discard telnet banner
        self._logger.debug(
            f"Telnet session read and discarded banner bytes {banner.hex()} "
            f"(raw string {repr(banner)})"
        )
        self._logger.debug(
            f"Telnet session sending request bytes {request.hex()} "
            f"(raw string {repr(request)})"
        )
        self._telnet_session.write(request)

        return _TelnetBytestringIterator(self._telnet_session)

    def close(self) -> None:
        """Close the connection and end the session."""
        self._telnet_session.close()
