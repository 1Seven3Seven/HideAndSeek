import struct
from enum import Enum

from .Constants import _ENDIANNESS


class BaseMessageInfo(Enum):
    def __new__(cls, value: object, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, _, format_string: str):
        """
        :param format_string:
            The format string for the message, not including the message indicator byte.
            Example, for an unsigned then signed int, "Ii".
            This should NOT include the endianness.
        """

        self.format_string: str = _ENDIANNESS + format_string
        """
        The format string used when unpacking with the python struct library.
        Does not include the header as that should be read to figure out what message should be unpacked.
        """

        self.format_string_with_indicator: str = _ENDIANNESS + "B" + format_string
        """The format string used when creating the message."""

    def create_bytes(self, *args) -> bytes:
        """
        Creates a bytes object with the format string using the supplied arguments.

        :param args: The arguments used to create the bytes object.
        :return: The bytes object.
        """

        # A format string always starts with the message indicator byte ("B" unsigned char)
        # This byte is stored in the _value_ property, hence why it is included here
        return struct.pack(self.format_string_with_indicator, self._value_, *args)

    @property
    def size_in_bytes(self) -> int:
        """
        Calculates and returns the size of the expected bytes object based off the format string.
        Does not include the indicator byte.
        Intended to be used to read the rest of the bytes from the socket after the indicator has been consumed.

        :return: The size of the expected bytes object.
        """

        return struct.calcsize(self.format_string)
