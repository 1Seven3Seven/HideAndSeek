import socket
import struct
import threading

from Logger import Logger
from Utils import ClientMessageInfo as ClientMI
from Utils import IndicatorInt
from Utils import ServerMessageInfo as ServerMI


class ClientHandler(Logger):
    def __init__(self, client_socket: socket.socket, client_address: tuple[str, int], client_id: int):
        self.socket: socket.socket = client_socket
        self.address: tuple[str, int] = client_address

        self.client_id: int = client_id

        self.handle_client_stop_event: threading.Event = threading.Event()
        self.handle_client_thread: threading.Thread | None = None

        self.__log_prepend: str = f"Client {client_id: 3} :"

    def log(self, *args, **kwargs):
        super().log(self.__log_prepend, *args, **kwargs)

    def perform_handshake(self) -> bool:
        """
        Performs the handshake with the client.

        :return: True if completed successfully, False otherwise.
        """

        self.log("Performing handshake")

        self.log("Waiting for indicator int")
        try:
            indicator_int = IndicatorInt.read_from_socket(self.socket)
        except (TimeoutError, struct.error) as e:
            self.log(f"Received error '{e}' when attempting to read the indicator")
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

        return True

    def handle_client(self) -> None:
        """
        Performs the handshake.
        If the handshake was successful, moves onto handling client messages and updating its state.
        """

        self.log("Handler thread started")

        handshake_result = self.perform_handshake()

        if not handshake_result:
            self.log("Handshake failed, closing socket")
            self.socket.close()
            return

        self.log("Handshake successful")

    def start(self) -> None:
        """
        Starts this client handler.
        """

        if self.handle_client_thread is not None:
            return

        self.log("Starting client handler thread")

        self.handle_client_stop_event.clear()

        self.handle_client_thread = threading.Thread(
            target=self.handle_client
        )
        self.handle_client_thread.start()

    def stop(self) -> None:
        """
        Stops this client handler.
        """

        if self.handle_client_thread is None:
            return

        self.log("Stopping client handler thread")

        self.handle_client_stop_event.set()
        self.handle_client_thread.join()
        self.handle_client_thread = None
