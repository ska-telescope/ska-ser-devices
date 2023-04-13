"""Unit tests of the client server module."""
import random
import string
import threading
from typing import Iterator

import pytest

from ska_ser_devices.client_server import (
    ApplicationClient,
    ApplicationServer,
    FixedLengthBytesMarshaller,
    SentinelBytesMarshaller,
    TcpClient,
    TcpServer,
)


@pytest.fixture(name="payload_length")
def payload_length_fixture() -> int:
    """
    Application-layer payload length.

    This is the length that will be used to generate a payload, for
    tests in which a fixed length marshaller will be used.

    :return: Application-layer payload length.
    """
    return 10000


@pytest.fixture(name="fixed_length_marshaller")
def fixed_length_marshaller_fixture(
    payload_length: int,
) -> FixedLengthBytesMarshaller:
    """
    Return a fixed-length marshaller.

    That is, a marshaller that marshals application-layer payloads to
    bytes, and vice-versa, on the basis that all payloads are a fixed
    length.

    :param payload_length: the fixed payload length

    :return: a fixed-length marshaller
    """
    return FixedLengthBytesMarshaller(payload_length)


@pytest.fixture(name="sentinel_marshaller")
def sentinel_marshaller_fixture() -> SentinelBytesMarshaller:
    """
    Return a sentinel marshaller.

    That is, a marshaller that marshals application-layer payloads to
    bytes, and vice-versa, on the basis that all payloads are terminated
    by a given sentinel character sequence.

    :return: a sentinel marshaller.
    """
    return SentinelBytesMarshaller(b"\n")


@pytest.fixture(name="reverse_server")
def reverse_server_fixture(
    fixed_length_marshaller: SentinelBytesMarshaller,
    sentinel_marshaller: FixedLengthBytesMarshaller,
) -> Iterator[TcpServer]:
    """
    Return a running server that provides a bytestring reversal service.

    Any bytestring sent to the server is sent back reversed.

    In order to test more than one marshaller,
    requests to the server are expected to be of a fixed length,
    but response are terminated by a sentinel.

    :param fixed_length_marshaller: a marshaller of fixed length
        application-layer payloads
    :param sentinel_marshaller: a marshaller of sentinel-terminated
        application-layer payloads

    :yield: a running server
    """
    application_server = ApplicationServer[bytes, bytes](
        fixed_length_marshaller.unmarshall,
        sentinel_marshaller.marshall,
        lambda request: bytes(reversed(request)),
    )
    tcp_server = TcpServer("localhost", 0, application_server)

    with tcp_server:
        server_thread = threading.Thread(
            name="Reverser server thread",
            target=tcp_server.serve_forever,
        )
        server_thread.daemon = True  # don't hang on exit
        server_thread.start()
        yield tcp_server
        tcp_server.shutdown()


@pytest.fixture(name="reverse_client")
def reverse_client_fixture(
    reverse_server: TcpServer,
    fixed_length_marshaller: FixedLengthBytesMarshaller,
    sentinel_marshaller: SentinelBytesMarshaller,
) -> ApplicationClient:
    """
    Return an application-layer client to the reversal server.

    In accordance with the server definition, requests to the server
    are sent as-is, but must have a fixed length. Responses received
    from the server are terminated by a sentinel.

    :param reverse_server: the running server that this client will
        communicate with.
    :param fixed_length_marshaller: a marshaller of fixed length
        application-layer payloads
    :param sentinel_marshaller: a marshaller of sentinel-terminated
        application-layer payloads

    :return: an application-layer client for the reversal server.
    """
    host, port = reverse_server.server_address
    tcp_client = TcpClient(host, port)
    application_client = ApplicationClient(
        tcp_client,
        fixed_length_marshaller.marshall,
        sentinel_marshaller.unmarshall,
    )
    return application_client


def test_client_server(reverse_client: ApplicationClient, payload_length: int) -> None:
    """
    Test client-server interactions.

    We generate a fixed length payload.
    We use the client to submit it to the server.
    We get back a response.
    We check that the response is the reversal of the original.

    :param reverse_client: the application-layer client
    :param payload_length: the payload length. This is required because
        the request protocol assumes a fixed length.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    request_str = "".join(random.choice(characters) for i in range(payload_length))
    request = request_str.encode("utf-8")

    response = reverse_client(request)

    assert response == bytes(reversed(request))
