from .BaseMessageInfo import BaseMessageInfo


class ClientMessageInfo(BaseMessageInfo):
    # Connecting or disconnecting from a server (0x0?)
    NEW_CONNECTION_REQUEST = 0x01, ""
    # RECONNECTION_REQUEST = 0x02, ""
    DISCONNECT_NOTIFICATION = 0x03, ""

    # Updating the servers information (0x2?)
    NAME_CHANGE_HEADER = 0x21, "I"
