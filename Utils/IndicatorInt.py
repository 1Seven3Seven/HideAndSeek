import socket
import struct

from .Constants import _ENDIANNESS


class IndicatorInt:
    """
    A special class for the indicator.
    """

    format_string = f"{_ENDIANNESS}B"
    size_in_bytes = struct.calcsize(format_string)

    @classmethod
    def read_from_socket(cls, soc: socket.socket) -> int:
        """
        Reads the amount required for an indicator int from the socket and converts it into an int.

        :param soc: The socket to read from.
        :return: The indicator int.
        :raises TimeoutError:
        :raises struct.error:
        """

        indicator_bytes = soc.recv(cls.size_in_bytes)
        indicator_int, = struct.unpack(cls.format_string, indicator_bytes)

        return indicator_int
