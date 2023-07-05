r"""
This module provides marshalling and unmarshalling for bytestring sequences.

Some transport protocols, such as TCP, deliver application payloads by
by breaking them up into multiple segments, which are delivered
separately (but in order). The receiving application may thus need to
read multiple buffers full of received bytes, in order to receive a
complete application payload. TCP does not tell the application when it
has finished transmitting data; it is up to the application layer to
know when it has received a complete transmission.

There are a few simple strategies for this. One is to mark the end of
a payload with a sentinel character sequence, such as an EOL or EOF.
Another is to make application payloads a known, fixed length.

This module implements some of these strategies.
"""

import logging
from typing import Iterator


class SentinelBytesMarshaller:
    r"""
    A bytes marshaller that marshalls and unmarshalls terminated bytestrings.

    That is, the application-layer payload is a bytestring,
    the end of which is demarcated by a special character sequence.
    For example, the payload might be

    * A c-style string, terminated by the NUL character;
    * A line of text, terminated by an end-of-line sequence, such as "\r\n".
    * A file, terminated by an EOF byte.
    """

    def __init__(self, sentinel: bytes, logger: logging.Logger | None = None) -> None:
        """
        Initialise a new instance.

        :param sentinel: the sentinel character that marks the end of
            the payload
        :param logger: a python standard logger
        """
        self._sentinel = sentinel
        self._logger = logger

    def marshall(self, payload: bytes) -> bytes:
        """
        Marshall application-layer payload bytes into bytes to be transmitted.

        This class simply appends the sentinel character sequence.

        :param payload: the application-layer payload bytes.

        :return: the bytes to be transmitted.
        """
        if self._logger:
            self._logger.debug(
                f"Marshalling payload {repr(payload)} "
                f"by appending sentinel {repr(self._sentinel)}"
            )
        return payload + self._sentinel

    def unmarshall(self, bytes_iterator: Iterator[bytes]) -> bytes:
        """
        Unmarshall transmitted bytes into application-layer payload bytes.

        This method is implemented to continually receive bytestrings
        until it receives a bytestring terminated by the sentinel.
        It then strips the sentinel off, and returns the rest.

        :param bytes_iterator: an iterator of bytestrings received
            by the server

        :return: the application-layer bytestring, minus the terminator.
        """
        payload = b""
        more_bytes = next(bytes_iterator)
        payload = payload + more_bytes

        while not more_bytes.endswith(self._sentinel):
            if self._logger:
                self._logger.debug(
                    f"Unmarshaller received payload bytes {repr(more_bytes)}, "
                    f"has not yet encountered sentinel {repr(self._sentinel)}"
                )
            more_bytes = next(bytes_iterator)
            payload = payload + more_bytes

        payload = payload.removesuffix(self._sentinel)
        if self._logger:
            self._logger.debug(
                f"Unmarshaller received payload bytes {repr(more_bytes)}, "
                f"encountered sentinel {repr(self._sentinel)}, "
                f"returning {repr(payload)}"
            )
        return payload


class FixedLengthBytesMarshaller:
    """A bytes marshaller for bytestrings of fixed, known length."""

    def __init__(self, length: int, logger: logging.Logger | None = None) -> None:
        """
        Initialise a new instance.

        :param length: the length of the payload
        :param logger: a python standard logger
        """
        self._length = length
        self._logger = logger

    def marshall(self, payload: bytes) -> bytes:
        """
        Marshall application-layer payload bytes into bytes to be transmitted.

        This class simply appends the sentinel character sequence.

        :param payload: the application-layer payload bytes.

        :return: the bytes to be transmitted.

        :raises ValueError: if the received bytestring is not of the
            correct length
        """
        if len(payload) != self._length:
            raise ValueError(
                f"Cannot marshall payload of length {len(payload)}; "
                f"length must be exactly {self._length}."
            )
        return payload

    def unmarshall(self, bytes_iterator: Iterator[bytes]) -> bytes:
        """
        Unmarshall transmitted bytes into application-layer payload bytes.

        This method is implemented to continually receive bytestrings
        until it receives a bytestring terminated by the sentinel.
        It then strips the sentinel off, and returns the rest.

        :param bytes_iterator: an iterator of bytestrings received
            by the server

        :return: the application-layer bytestring.

        :raises ValueError: if the received bytestring is not of the
            correct length
        """
        payload = b""
        more_bytes = next(bytes_iterator)
        payload = payload + more_bytes

        while len(payload) < self._length:
            if self._logger:
                self._logger.debug(
                    f"Unmarshaller received payload bytes {repr(more_bytes)}, "
                    f"payload is incomplete: {len(payload)} < {self._length}"
                )
            more_bytes = next(bytes_iterator)
            payload = payload + more_bytes

        if len(payload) != self._length:
            raise ValueError(
                f"Cannot unmarshall payload of length {len(payload)}; "
                f"length must be exactly {self._length}."
            )
        if self._logger:
            self._logger.debug(
                f"Unmarshaller received payload bytes {repr(more_bytes)}, "
                f"payload is complete, returning {repr(payload)}"
            )
        return payload
