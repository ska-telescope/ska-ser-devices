"""This module contains unit tests of the package version."""
import ska_ser_devices


def test_version() -> None:
    """Test that the package version is as expected."""
    assert ska_ser_devices.__version__ == "0.2.0"
