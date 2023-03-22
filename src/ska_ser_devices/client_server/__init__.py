r"""
This subpackage supports client-server communication.

A key design element is that received data is provided to the
application layer via a bytestring iterator:

Receipt of an application payload may be split across multiple buffers,
and the manner by which the application layer decides
that it has received enough bytes to comprise a full application payload
is application-dependent.

For example, the application layer might deal in "lines",
and receiving a "line" might involve continually receiving bytestrings
until a line terminator character sequence such as "\r\n" is encountered.

Using TCP as an example, this concatenation of bytestrings into an
application payload is typically implemented like:

.. code-block:: python

    data = my_socket.recv(1024)
    while not data.endswith(b"\r\n"):
        data = data + my_socket.recv(1024)

but this approach mixes transport protocol details (e.g socket reads)
with application-level decision logic.

Instead, this module handles this situation
by passing a bytestring iterator to the application layer.
Thus, it is the application layer's job to iterate over bytestrings
until it has constructed a full application payload.
Meanwhile, the transport protocol details remain hidden.

.. code-block:: python

    data = next(bytes_iterator)
    while not data.endswith(b"\r\n"):
        data = data + next(bytes_iterator)
"""
__all__ = [
    "TcpClient",
    "TcpServer",
    "TelnetClient",
    "FixedLengthBytesMarshaller",
    "SentinelBytesMarshaller",
    "ApplicationClient",
    "ApplicationServer",
    "TransportClientProtocol",
]

from .application import (
    ApplicationClient,
    ApplicationServer,
    TransportClientProtocol,
)
from .marshaller import FixedLengthBytesMarshaller, SentinelBytesMarshaller
from .tcp import TcpClient, TcpServer
from .telnet import TelnetClient
