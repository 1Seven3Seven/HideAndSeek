import socket
import struct
import threading

from Logger import Logger
from Utils import ClientMessageInfo as ClientMI
from Utils import IndicatorInt
from Utils import ServerMessageInfo as ServerMI


class ServerState(Logger):
    def __init__(self, client_socket: socket.socket):
        self.socket: socket.socket = client_socket

        self.client_id: int = 0

        self.state_updater_stop_event: threading.Event = threading.Event()
        self.state_updater_thread: threading.Thread | None = None

    def perform_handshake(self) -> bool:
        """
        Performs the handshake with the server.

        :return: True if completed successfully, False otherwise.
        """

        self.log("Sending connection request")
        try:
            self.socket.sendall(
                ClientMI.NEW_CONNECTION_REQUEST.create_bytes()
            )
        except OSError as e:
            self.log(f"Error with connection '{e}'")
            return False

        self.log("Waiting for indicator int")
        try:
            indicator_int = IndicatorInt.read_from_socket(self.socket)
        except (TimeoutError, struct.error) as e:
            self.log(f"Received error '{e}' when attempting to read the indicator")
            return False
        self.log(f"Indicator int is {indicator_int}")

        if indicator_int != ServerMI.CLIENT_SET_ID.value:
            self.log("Incorrect indicator int")
            return False

        self.log("Reading client id bytes")
        try:
            client_id_bytes = self.socket.recv(
                ServerMI.CLIENT_SET_ID.size_in_bytes
            )
        except TimeoutError:
            self.log("Connection timed out")
            return False

        self.log("Converting client id bytes to client id int")
        try:
            client_id_int, = struct.unpack(
                ServerMI.CLIENT_SET_ID.format_string,
                client_id_bytes
            )
        except struct.error as e:
            self.log(f"Received error '{e}'")
            return False

        self.log(f"Client id is {client_id_int}")
        self.client_id = client_id_int

        return True

    def state_updater(self) -> None:
        self.log("State updater thread started")

        handshake_result = self.perform_handshake()

        if not handshake_result:
            self.log("Handshake failed, closing socket")
            self.socket.close()
            return

        self.log("Handshake successful")

    def start_updater(self) -> None:
        if self.state_updater_thread is not None:
            return

        self.log("Starting state updater thread")

        self.state_updater_stop_event.clear()

        self.state_updater_thread = threading.Thread(
            target=self.state_updater
        )
        self.state_updater_thread.start()

    def stop_updater(self) -> None:
        if self.state_updater_thread is None:
            return

        self.log("Stopping state updater thread")

        self.state_updater_stop_event.set()
        self.state_updater_thread.join()
        self.state_updater_thread = None
