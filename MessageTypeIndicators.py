from enum import Enum


class _MessageInfo(Enum):
    def __new__(cls, value: object, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, _, format_string: str):
        self.format_string: str = format_string
        """The format string used when packing/unpacking with the python struct library"""


class ServerMessageInfo(_MessageInfo):
    # Handling client connections and disconnections (0x0?)
    CLIENT_SET_ID = 0x01, "<BI"
    CLIENT_TO_DISCONNECT = 0x02, "<B"
    CLIENT_RECONNECT_ACCEPTED = 0x03, "<B"
    CLIENT_RECONNECT_REJECTED = 0x04, "<B"

    # Transferring map and position data (0x1?)
    MAP_DATA_HEADER = 0x11, "<BII"
    STARTING_POSITION = 0x12, "<Bii"

    # Updating client information (0x02?)
    CLIENT_NAME_ACCEPTED = 0x21, "<B"
    CLIENT_NAME_REJECTED = 0x22, "<B"
    CLIENT_NEW_NAME_HEADER = 0x23, "<BII"
    CLIENT_CONNECTED_NOTIFICATION = 0x24, "<BI"
    CLIENT_DISCONNECTED_NOTIFICATION = 0x25, "<BI"

    # Misc (0xF?)
    START_GAME = 0xF1, "<B"


class ClientMessageInfo(_MessageInfo):
    # Connecting or disconnecting from a server (0x0?)
    NEW_CONNECTION_REQUEST = 0x01, "<B"
    RECONNECTION_REQUEST = 0x02, "<B"

    # Updating the servers information (0x2?)
    NAME_CHANGE_HEADER = 0x21, "<BI"
