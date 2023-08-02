r"""
This subpackage supports client-server communication.

A key design element is that received data is provided to the
application layer via a bytestring iterator:

Receipt of an application payload may be split across multiple buffers,
and the manner by which the application layer decides
that it has received enough bytes to comprise a full application payload
is exclusively determined by the application.

For example, the application layer might deal in "lines",
and receiving a "line" might involve continually receiving bytestrings
until a line terminator character sequence such as "\r\n" is encountered.

Using TCP as an example for how transport protocol details (e.g. socket
reads) are commonly mixed with application-level decision logic,
the concatenation of bytestrings into an application payload
is typically implemented like:

.. code-block:: python

    data = my_socket.recv(1024)
    while not data.endswith(b"\r\n"):
        data = data + my_socket.recv(1024)

Instead, this module handles this situation
by passing a bytestring iterator to the application layer.
Thus, it is the application layer's job to iterate over bytestrings
until it has constructed a full application payload.
Meanwhile, the transport protocol details remain hidden,
and the application remains agnostic of any transport mechanism.

.. code-block:: python

    data = next(bytes_iterator)
    while not data.endswith(b"\r\n"):
        data = data + next(bytes_iterator)
"""
__all__ = [
    "TcpClient",
    "TcpServer",
    "TelnetClient",
    "Telnet3Client",
    "Telnet3Server",
    "FixedLengthBytesMarshaller",
    "SentinelBytesMarshaller",
    "ApplicationClient",
    "ApplicationServer",
    "TransportClientProtocol",
]

from .application import ApplicationClient, ApplicationServer, TransportClientProtocol
from .marshaller import FixedLengthBytesMarshaller, SentinelBytesMarshaller
from .tcp import TcpClient, TcpServer
from .telnet import TelnetClient
from .telnet3 import Telnet3Client, Telnet3Server
