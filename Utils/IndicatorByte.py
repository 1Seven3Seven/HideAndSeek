import struct

from .Constants import _ENDIANNESS


class IndicatorByte:
    """
    A special class for the indicator.
    """

    format_string = f"{_ENDIANNESS}B"
    size_in_bytes = struct.calcsize(format_string)

    @classmethod
    def create_bytes(cls, indicator: int) -> bytes:
        return struct.pack(cls.format_string, indicator)
