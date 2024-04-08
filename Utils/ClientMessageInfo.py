from .BaseMessageInfo import BaseMessageInfo


class ClientMessageInfo(BaseMessageInfo):
    # Connecting or disconnecting from a server (0x1?)
    NEW_CONNECTION_REQUEST = 0x11, ""
    WILL_DISCONNECT = 0x12, ""
