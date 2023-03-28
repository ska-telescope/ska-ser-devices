r"""This module provides a Telnet client."""
from __future__ import annotations

from contextlib import contextmanager
from telnetlib import Telnet
from typing import Iterator, Optional


class _TelnetBytestringIterator:
    """An iterator on Telnet byte buffers."""

    def __init__(self, session: Telnet) -> None:
        """
        Initialise a new instance.

        :param session: the Telnet session
        """
        self._session = session

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
        """
        return self._session.read_some()


# pylint: disable-next=too-few-public-methods
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
        host: str,
        port: int,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Initialise a new instance.

        :param host: host name or IP address of the server.
        :param port: port on which the server is running.
        :param timeout: how long to wait when attempting to send or
            receive data.
        """
        self._host = host
        self._port = port
        self._timeout = timeout

    @contextmanager
    def request(self, request: bytes) -> Iterator[Iterator[bytes]]:
        r"""
        Initiate a new client request.

        Call this method like

        .. code-block:: python

            with telnet_client.request(request_bytes) as bytes_iterator:
                response_bytes = next(bytes_iterator)
                if not response_bytes.endswith(b"\r\n"):
                    response_bytes += next(bytes_iterator)

        That is,

        * First enter into a session with the Telnet server
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
        # Oh, this is nasty.
        if self._timeout is None:
            session = Telnet(self._host, self._port)
        else:
            session = Telnet(self._host, self._port, self._timeout)

        session.read_some()  # read and discard telnet banner
        session.write(request)

        yield _TelnetBytestringIterator(session)

        session.close()
