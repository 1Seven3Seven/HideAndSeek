import socket
import struct
import threading

import select

from Utils import *


class ClientHandler(Logger):
    def __init__(self, client_id: int, client_socket: socket.socket, client_address: tuple[str, int]):
        self.client_id: int = client_id

        self.socket: socket.socket = client_socket
        self.address: tuple[str, int] = client_address

        self._is_alive: bool = True

        self._handler_stop_event: threading.Event = threading.Event()
        self._handler_thread: threading.Thread | None = None

    def log(self, *args, **kwargs):
        super().log(f"Client {self.client_id}:", *args, **kwargs)

    @property
    def is_alive(self) -> bool:
        """
        Determines if this client is alive and returns a boolean value based on the result.

        :return: True if the client is alive, otherwise False.
        """

        return self._is_alive

    def _handler(self) -> None:
        """
        Handles any messages being sent to the server from the client.
        """

        _prepend = "Handler:"

        while not self._handler_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if not readable:
                continue

            try:
                indicator_int = IndicatorInt.read_from_socket(self.socket)
            except (OSError, struct.error) as e:
                self.log(_prepend, f"Received error '{e}', closing socket")
                self.socket.close()
                break

            if indicator_int == ClientMessageInfo.WILL_DISCONNECT.value:
                self.log(_prepend, "Client will disconnect, closing socket")
                self.socket.close()
                self._is_alive = False
                break

            else:
                self.log(_prepend, f"Received unknown/unhandled indicator int {hex(indicator_int)}, closing socket")
                self.socket.close()
                self._is_alive = False
                break

        self.log(_prepend, "Thread terminating")

    def start(self) -> None:
        if self._handler_thread is not None:
            return

        self.log("Starting client handler")

        self._handler_stop_event.clear()

        self._handler_thread = threading.Thread(
            target=self._handler
        )
        self._handler_thread.start()

    def stop(self) -> None:
        if self._handler_thread is None:
            return

        self.log("Stopping client handler")

        self._handler_stop_event.set()
        self._handler_thread.join()
        self._handler_thread = None
