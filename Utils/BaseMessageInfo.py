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
        """The format string used when packing/unpacking with the python struct library"""

    def create_bytes(self, *args) -> bytes:
        """
        Creates a bytes object with the format string using the supplied arguments.

        :param args: The arguments used to create the bytes object.
        :return: The bytes object.
        """

        # A format string always starts with the message indicator byte ("B" unsigned char)
        # This byte is stored in the _value_ property, hence why it is included here
        return struct.pack(self.format_string, self._value_, *args)

    @property
    def size_in_bytes(self) -> int:
        """
        Calculates and returns the size of the expected bytes object based off the format string.

        :return: The size of the expected bytes object.
        """

        return struct.calcsize(self.format_string)
