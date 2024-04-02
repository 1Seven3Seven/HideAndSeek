import struct
from enum import Enum

_ENDIANNESS = "<"


class IndicatorByte:
    """
    A special class for the indicator.
    """

    format_string = f"{_ENDIANNESS}B"
    size_in_bytes = struct.calcsize(format_string)

    @classmethod
    def create_bytes(cls, indicator: int) -> bytes:
        return struct.pack(cls.format_string, indicator)


class _MessageInfo(Enum):
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


class ServerMessageInfo(_MessageInfo):
    # Handling client connections and disconnections (0x0?)
    CLIENT_SET_ID = 0x01, "I"
    # CLIENT_TO_DISCONNECT = 0x02, ""
    # CLIENT_RECONNECT_ACCEPTED = 0x03, ""
    # CLIENT_RECONNECT_REJECTED = 0x04, ""

    # Transferring map and position data (0x1?)
    # MAP_DATA_HEADER = 0x11, "II"
    # STARTING_POSITION = 0x12, "ii"

    # Updating client information (0x02?)
    CLIENT_NAME_ACCEPTED = 0x21, ""
    CLIENT_NAME_REJECTED = 0x22, ""
    CLIENT_NEW_NAME_HEADER = 0x23, "II"
    CLIENT_CONNECTED_NOTIFICATION = 0x24, "I"
    CLIENT_DISCONNECTED_NOTIFICATION = 0x25, "I"

    # Misc (0xF?)
    # START_GAME = 0xF1, ""


class ClientMessageInfo(_MessageInfo):
    # Connecting or disconnecting from a server (0x0?)
    NEW_CONNECTION_REQUEST = 0x01, ""
    # RECONNECTION_REQUEST = 0x02, ""
    DISCONNECT_NOTIFICATION = 0x03, ""

    # Updating the servers information (0x2?)
    NAME_CHANGE_HEADER = 0x21, "I"
