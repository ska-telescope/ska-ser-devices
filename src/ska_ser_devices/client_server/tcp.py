"""This module provides a TCP server and client."""
from __future__ import annotations

import socket
import socketserver
from contextlib import contextmanager
from typing import Callable, Final, Iterator, Optional, Union, cast

DEFAULT_BUFFER_SIZE: Final = 1024


class _TcpBytestringIterator:
    """An iterator on TCP byte buffers."""

    def __init__(
        self, tcp_socket: socket.socket, buffer_size: int = DEFAULT_BUFFER_SIZE
    ) -> None:
        """
        Initialise a new instance.

        :param tcp_socket: the socket on which to receive bytestrings
        :param buffer_size: maximum size of a received bytestring
        """
        self._socket = tcp_socket
        self._buffer_size = buffer_size

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
            raise StopIteration()  # not essential but helpful for debugging
        return bytestring


class _TcpServerRequestHandler(socketserver.BaseRequestHandler):
    """Request handler for a Bytestring TCP server."""

    def handle(self) -> None:
        """Handle a client request."""
        server = cast(TcpServer, self.server)

        bytes_iterator = _TcpBytestringIterator(
            self.request, server.buffer_size
        )
        response = server.callback(bytes_iterator)
        if response:
            self.request.sendall(response)


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

    def __init__(
        self,
        host: str,
        port: int,
        callback: Callable[[Iterator[bytes]], Optional[bytes]],
        buffer_size: int = DEFAULT_BUFFER_SIZE,
    ) -> None:
        """
        Initialise a new instance.

        :param host: host name or IP address of the server.
        :param port: port on which the server is running.
        :param callback: the application layer callback to call when
            bytes are received
        :param buffer_size: maximum size of a bytestring.
        """
        self.callback: Final = callback
        self.buffer_size: Final = buffer_size

        super().__init__((host, port), _TcpServerRequestHandler)


# pylint: disable-next=too-few-public-methods
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
        host: Union[str, bytes, bytearray],
        port: int,
        timeout: Optional[float] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
    ) -> None:
        """
        Initialise a new instance.

        :param host: host name or IP address of the server.
        :param port: port on which the server is running.
        :param timeout: how long to wait when attempting to send or
            receive data.
        :param buffer_size: maximum size of a bytestring.
        """
        self._host = host
        self._port = port
        self._timeout = timeout
        self._buffer_size = buffer_size

    @contextmanager
    def request(self, request: bytes) -> Iterator[Iterator[bytes]]:
        r"""
        Initiate a new client request.

        Call this method with

        .. code-block:: python

            with tcp_client.request(request_bytes) as bytes_iterator:
                response_bytes = next(bytes_iterator)
                if not response_bytes.endswith(b"\r\n"):
                    response_bytes += next(bytes_iterator)

        That is,

        * First enter into a session with the TCP server
          by establishing a connection and sending the request data.
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

        :yields: a bytestring iterator.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._host, self._port))
        sock.settimeout(self._timeout)
        sock.sendall(request)
        yield _TcpBytestringIterator(sock, self._buffer_size)
        sock.close()
