"""This module provides a TCP server and client."""
from __future__ import annotations

import logging
import socket
import socketserver
from types import TracebackType
from typing import Callable, Final, Iterator, Type, cast

DEFAULT_BUFFER_SIZE: Final = 1024


_module_logger = logging.getLogger(__name__)


class _TcpBytestringIterator:
    """An iterator on TCP byte buffers."""

    def __init__(
        self,
        tcp_socket: socket.socket,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise a new instance.

        :param tcp_socket: the socket on which to receive bytestrings
        :param buffer_size: maximum size of a received bytestring
        :param logger: a python standard logger
        """
        self._socket = tcp_socket
        self._buffer_size = buffer_size
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

        :raises StopIteration: if the socket performs an empty read.
        """
        bytestring = self._socket.recv(self._buffer_size)
        if not bytestring:
            self._logger.debug("TCP socket received no bytes.")
            raise StopIteration()  # not essential but helpful for debugging

        self._logger.debug(
            f"TCP socket received bytes {bytestring.hex()} "
            f"(raw string {repr(bytestring)})"
        )
        return bytestring


class _TcpServerRequestHandler(socketserver.BaseRequestHandler):
    """Request handler for a Bytestring TCP server."""

    def handle(self) -> None:
        """Handle a client request."""
        server = cast(TcpServer, self.server)
        server.logger.debug(f"TCP server handling request: {repr(self.request)}")

        while True:
            bytes_iterator = _TcpBytestringIterator(self.request, server.buffer_size)
            try:
                response = server.callback(bytes_iterator)
            except StopIteration:
                break
            if response:
                server.logger.debug(f"TCP server responding with: {repr(response)}")
                self.request.sendall(response)
            else:
                server.logger.debug("TCP server not responding to request")


class TcpServer(socketserver.TCPServer):
    """
    A TCP server that operates at the bytestring level.

    It handles client requests by creating a bytestring iterator,
    and handing it up to the application layer,
    so that the application layer can receive as many bytestrings
    as it needs to constitute an application payload.
    When the application layer returns a response,
    that response is sent back to the client.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        port: int,
        callback: Callable[[Iterator[bytes]], bytes | None],
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise a new instance.

        :param host: host name or IP address of the server.
        :param port: port on which the server is running.
        :param callback: the application layer callback to call when
            bytes are received
        :param buffer_size: maximum size of a bytestring.
        :param logger: a python standard logger
        """
        self.callback: Final = callback
        self.buffer_size: Final = buffer_size
        self.logger = logger or _module_logger

        super().__init__((host, port), _TcpServerRequestHandler)


class TcpClient:
    """
    A TCP client that operates at the bytestring level.

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
        address: tuple[str | bytes | bytearray, int],
        timeout: float | None = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise a new instance.

        :param address: tuple consisting of
            the host name or IP address, and the port, of the server.
        :param timeout: how long to wait when attempting to send or
            receive data, in seconds. If None, the socket blocks
            indefinitely.
        :param buffer_size: maximum size of a bytestring.
        :param logger: a python standard logger
        """
        self._address = address
        self._timeout = timeout
        self._buffer_size = buffer_size
        self._logger = logger or _module_logger

        self._session: TcpClientSession | None = None
        self._logger.debug("TCP client initialised.")

    def connect(self) -> TcpClientSession:
        """
        Establish a new connection.

        :return: access to the established session.
        """
        self._logger.debug("Creating TCP client session...")
        self._session = TcpClientSession(
            self._address, self._timeout, self._buffer_size, self._logger
        )
        return self._session

    def __enter__(self) -> TcpClientSession:
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


class TcpClientSession:
    """A class for representing and managing a TCP session."""

    def __init__(
        self,
        address: tuple[str | bytes | bytearray, int],
        timeout: float | None,
        buffer_size: int,
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
        :param buffer_size: maximum size of a bytestring.
        :param logger: a python standard logger
        """
        self._logger = logger
        self._buffer_size = buffer_size

        self._logger.info(f"TCP client connecting to {address}...")
        self._session_socket: socket.socket | None = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self._session_socket.settimeout(timeout)
        self._session_socket.connect(address)
        self._logger.info("TCP client connection established.")

    def request(self, request: bytes) -> Iterator[bytes]:
        r"""
        Initiate a new client request.

        For example:

        .. code-block:: python

            with tcp_client as session:
                bytes_iterator = session.request(request_bytes):
                response_bytes = next(bytes_iterator)
                if not response_bytes.endswith(b"\r\n"):
                    response_bytes += next(bytes_iterator)

        That is,

        * First enter into a session with the TCP server
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

        :raises ConnectionError: if the session socket is already closed.

        :return: a bytestring iterator.
        """
        if not self._session_socket:
            raise ConnectionError("Session socket is closed.")

        self._logger.debug(
            f"TCP client sending request bytes {request.hex()} "
            f"(raw string {repr(request)})"
        )
        self._session_socket.sendall(request)
        return _TcpBytestringIterator(self._session_socket, self._buffer_size)

    def close(self) -> None:
        """Close the connection and end the session."""
        if self._session_socket:
            self._session_socket.close()
            self._session_socket = None
        self._logger.info("TCP client closed connection.")
