import queue
import socket
import struct
import threading

from ClientHandler import ClientHandler
from UpdaterTask import UpdaterTask
from UpdaterTaskTypes import UpdaterTaskTypes
from Utils import *


class ClientHandlerManager:
    """
    A class to manage all client connections to the server.

    Manages threads to update information sent from the client to the server.
    """

    def __init__(self):
        self.modifier_lock: threading.Lock = threading.Lock()
        """A lock that must be acquired before modifying self.client_handlers"""

        self.client_id_to_handler: dict[int, ClientHandler] = {}
        """A dictionary of all the 'alive' client ids to their handler."""

        self.updater_tasks: queue.Queue[UpdaterTask] = queue.Queue()
        """A queue of tasks for which contain information pertaining how to update clients."""

        self.updater_stop_event: threading.Event = threading.Event()
        self.updater_thread: threading.Thread | None = None

    def handle_client(self, client_id: int, client_socket: socket.socket, client_address: tuple[str, int]) -> None:
        """
        Sets up and starts a client handler for the given client with id, socket and address.

        :param client_id: The id of the client to be handled.
        :param client_socket: The socket connection to the client to be handled.
        :param client_address: The address of the client to be handled.
        """

        Logger.log(f"Handling client with id {client_id} at address {client_address[0]}:{client_address[1]}")

        client_handler = ClientHandler(client_id, client_socket, client_address, self.updater_tasks)

        with self.modifier_lock:
            self.client_id_to_handler[client_id] = client_handler

        self.updater_tasks.put(UpdaterTask(UpdaterTaskTypes.NUM_CLIENTS_CHANGED))

        client_handler.start()

    def remove_client(self, client_id: int) -> None:
        """
        Removes the client with the given `client id` if it exists.
        Stops the handler thread for that client and closes the socket.

        :param client_id: The id of the client to remove.
        """

        if client_id not in self.client_id_to_handler:
            return

        self.client_id_to_handler[client_id].stop()

        with self.modifier_lock:
            del self.client_id_to_handler[client_id]

    def __handle_num_clients_changed(self) -> None:
        """
        A blanket function that looks for any 'dead' clients and removes their handlers.
        Then updates each client with the new list of client ids.
        """

        Logger.log("Finding and removing any 'dead' clients")
        with self.modifier_lock:
            dead_client_ids = [
                client_id for client_id, handler in self.client_id_to_handler.items() if not handler.is_alive
            ]

            for client_id in dead_client_ids:
                self.client_id_to_handler[client_id].stop()
                del self.client_id_to_handler[client_id]

            client_id_tuple = tuple(self.client_id_to_handler.keys())
            client_handler_tuple = tuple(self.client_id_to_handler.values())
        client_id_tuple_len = len(client_id_tuple)

        Logger.log("Creating message to send")
        bytes_to_send = \
            ServerMessageInfo.CONNECTED_CLIENT_IDS_HEADER.create_bytes(client_id_tuple_len) \
            + struct.pack("I" * client_id_tuple_len, *client_id_tuple)

        Logger.log("Sending bytes")
        need_to_re_update = False
        client_handler: ClientHandler
        for client_handler, client_id in zip(client_handler_tuple, client_id_tuple):
            try:
                client_handler.socket.sendall(bytes_to_send)
            except OSError as e:
                Logger.log(f"Sending to client id {client_id} caused error '{e}'")
                client_handler.socket.close()
                with self.modifier_lock:
                    del self.client_id_to_handler[client_id]
                need_to_re_update = True

        if need_to_re_update:
            Logger.log("Re-adding NUM_CLIENTS_CHANGED task")
            self.updater_tasks.put(UpdaterTask(UpdaterTaskTypes.NUM_CLIENTS_CHANGED))

    def updater(self) -> None:

        Logger.log("Thread started")

        while not self.updater_stop_event.is_set():
            try:
                task = self.updater_tasks.get(timeout=0.1)
            except queue.Empty:
                continue

            if task.task == UpdaterTaskTypes.NUM_CLIENTS_CHANGED:
                Logger.log("Handling NUM_CLIENTS_CHANGED")
                self.__handle_num_clients_changed()

            else:
                Logger.log(f"Encountered unknown task '{task.task}'")

        Logger.log("Thread terminating")

    def start(self) -> None:
        if self.updater_thread is not None:
            return

        Logger.log("Starting updater thread")

        self.updater_stop_event.clear()

        self.updater_thread = threading.Thread(
            target=self.updater
        )
        self.updater_thread.start()

    def stop(self) -> None:
        if self.updater_thread is None:
            return

        Logger.log("Stopping updater thread")

        self.updater_stop_event.set()
        self.updater_thread.join()
        self.updater_thread = None

    def shutdown(self) -> None:
        Logger.log("Shutting down")

        self.stop()

        with self.modifier_lock:
            for client_handler in self.client_id_to_handler.values():
                client_handler.socket.close()
                client_handler.stop()
