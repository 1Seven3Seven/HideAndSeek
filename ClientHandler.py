import socket
import struct
import threading

from Logger import Logger
from Utils import ClientMessageInfo as ClientMI
from Utils import IndicatorByte
from Utils import ServerMessageInfo as ServerMI


class ClientHandler(Logger):
    def __init__(self, client_socket: socket.socket, client_address: tuple[str, int], client_id: int):
        self.socket: socket.socket = client_socket
        self.address: tuple[str, int] = client_address

        self.client_id: int = client_id

        self.handle_client_stop_event: threading.Event = threading.Event()
        self.handle_client_thread: threading.Thread | None = None

        self.prepend: str = f"Client {client_id: 3} :"

    def log(self, *args, **kwargs):
        super().log(self.prepend, *args, **kwargs)

    def perform_handshake(self) -> bool:
        """
        Performs the handshake with the client.
        Closes the socket if at any point it fails.

        :return: True if completed successfully, False otherwise.
        """

        self.log("Performing handshake")

        self.log("Waiting for indicator bytes")
        try:
            indicator_bytes = self.socket.recv(
                IndicatorByte.size_in_bytes
            )
        except TimeoutError:
            self.log("Connection timed out")
            return False

        self.log("Converting to integer")
        try:
            indicator_int, = struct.unpack(
                IndicatorByte.format_string,
                indicator_bytes
            )
        except struct.error as e:
            self.log(f"Received error '{e}'")
            return False
        self.log(f"Indicator int is {indicator_int}")

        if indicator_int != ClientMI.NEW_CONNECTION_REQUEST.value:
            self.log("Incorrect indicator int")
            return False

        self.log("Sending client id to client")
        try:
            self.socket.sendall(
                ServerMI.CLIENT_SET_ID.create_bytes(self.client_id)
            )
        except OSError as e:
            self.log(f"Received error '{e}'")
            return False

        # All done
        return True

    def handle_client(self) -> None:
        self.log("Handler thread started")

        handshake_result = self.perform_handshake()

        if not handshake_result:
            self.log("Handshake failed, closing socket")
            self.socket.close()
            return

        self.log("Handshake successful")
        return

    def start(self) -> None:
        """
        Starts this client handler.
        """

        if self.handle_client_thread is not None:
            return

        self.log("Starting client handler")

        self.handle_client_stop_event.clear()

        self.handle_client_thread = threading.Thread(
            target=self.handle_client
        )
        self.handle_client_thread.start()
