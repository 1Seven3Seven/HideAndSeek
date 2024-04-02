from .BaseMessageInfo import BaseMessageInfo


class ServerMessageInfo(BaseMessageInfo):
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
