from .BaseMessageInfo import BaseMessageInfo


class ServerMessageInfo(BaseMessageInfo):
    # Handling client connections and disconnections (0x1?)
    CLIENT_ID = 0x11, "I"

    # Updating client information (0x02?)
    CONNECTED_CLIENT_IDS_HEADER = 0x21, "I"  # The number of connected clients followed by all the client id numbers
