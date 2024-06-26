import queue
import socket
import struct
import threading

import select

from UpdaterTask import UpdaterTask
from UpdaterTaskTypes import UpdaterTaskTypes
from Utils import *


class ClientHandler(Logger):
    """
    A class to manage a single client.

    Maintains a thread to update information being sent from the client.
    """

    def __init__(self,
                 client_id: int,
                 client_socket: socket.socket, client_address: tuple[str, int],
                 updater_queue: queue.Queue[UpdaterTask]):
        """
        :param client_id: The id of the client to be handled.
        :param client_socket: The socket connection to the client.
        :param client_address: The address of the client.
        :param updater_queue: The queue to put tasks in pertaining information to be sent to other clients.
        """

        self.log(f"Creating client handler for id {client_id} at {client_address[0]}:{client_address[1]}")

        self.client_id: int = client_id

        self.socket: socket.socket = client_socket
        self.address: tuple[str, int] = client_address

        self._is_alive: bool = True

        self.updater_queue: queue.Queue[UpdaterTask] = updater_queue

        self._handler_stop_event: threading.Event = threading.Event()
        self._handler_thread: threading.Thread | None = None

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

        Logger.log("Thread started")

        while not self._handler_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if not readable:
                continue

            try:
                indicator_int = IndicatorInt.read_from_socket(self.socket)
            except (OSError, struct.error) as e:
                self.log(f"Received error '{e}'")
                break

            if indicator_int == ClientMessageInfo.WILL_DISCONNECT.value:
                self.log("Client will disconnect")
                break

            else:
                self.log(f"Received unknown/unhandled indicator int {hex(indicator_int)}")
                break

        Logger.log("Closing socket")
        self.socket.close()
        self._is_alive = False

        self.updater_queue.put(UpdaterTask(UpdaterTaskTypes.NUM_CLIENTS_CHANGED))

        self.log("Thread terminating")

    def start(self) -> None:
        """
        Starts the internal thread to handle any messages received from the client.
        """

        if self._handler_thread is not None:
            return

        self.log("Starting client handler")

        self._handler_stop_event.clear()

        self._handler_thread = threading.Thread(
            target=self._handler
        )
        self._handler_thread.start()

    def stop(self) -> None:
        """
        Stops the internal thread to handle any messages received from the client.
        """

        if self._handler_thread is None:
            return

        self.log("Stopping client handler")

        self._handler_stop_event.set()
        self._handler_thread.join()
        self._handler_thread = None
