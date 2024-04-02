import queue
import socket
import struct
import threading
from enum import Enum, auto
from ipaddress import IPv4Address
from typing import Any

import select

from MessageTypeIndicators import ClientMessageInfo, IndicatorByte, ServerMessageInfo


class _ServerTasks(Enum):
    INFORM_CLIENT_NAME = auto()
    INFORM_CLIENT_CONNECTED = auto()
    INFORM_CLIENT_DISCONNECTED = auto()


class Server:
    def __init__(self, ip: IPv4Address, port: int):
        self.ip: IPv4Address = ip
        self.port: int = port

        self.socket: socket.socket = socket.socket()
        self.socket.bind((str(ip), port))
        self.socket.listen()

        self.accept_clients_thread: threading.Thread | None = None
        self.accept_clients_stop_event: threading.Event = threading.Event()

        self.next_client_id: int = 1

        # Handling a client connection

        self.client_id_to_socket: dict[int, socket.socket] = {}
        self.client_id_to_address: dict[int, tuple[str, int]] = {}
        self.client_id_to_stop_event: dict[int, threading.Event] = {}
        self.client_id_to_handler_thread: dict[int, threading.Thread] = {}

        # Client information

        self.client_id_to_name: dict[int, str] = {}

        # Updating client information

        self.client_updater_stop_event: threading.Event = threading.Event()
        self.client_updater_task_queue: queue.Queue[tuple[_ServerTasks, tuple[Any, ...]]] = queue.Queue()
        """
        A queue containing tuples with the first item always being a server task and the second is a tuple containing 
        the information for that task.
        """
        self.client_updater_thread: threading.Thread | None = None

        # For neat viewing of information
        self.printer_lock: threading.Lock = threading.Lock()

    def print(self, *_args, **_kwargs):
        with self.printer_lock:
            print(*_args, **_kwargs)

    def delete_information_regarding_client_id(self, client_id: int) -> None:
        """
        Delete information regarding client id.
        Can be called from inside a thread, although the thread must return immediately afterward.

        :param client_id: The client id whose information is to be deleted.
        """

        self.print(f"Server: Deleting information for client id {client_id}")

        del self.client_id_to_socket[client_id]
        del self.client_id_to_address[client_id]
        del self.client_id_to_stop_event[client_id]
        del self.client_id_to_handler_thread[client_id]
        del self.client_id_to_name[client_id]

    def setup_client_from_socket_address(self, client_socket: socket.socket, client_address: tuple[str, int]) -> None:
        """
        Sets up the necessary information regarding a client from its socket.
        Creates the handler thread and starts it.
        Finally, increments the next_client_id for the nex call.

        :param client_socket: The client socket that was created.
        :param client_address: The address of the client socket.
        """

        self.print(f"Server : New client with address {client_address} under client id {self.next_client_id}")

        # Set up the handling information

        self.client_id_to_socket[self.next_client_id] = client_socket
        self.client_id_to_address[self.next_client_id] = client_address
        self.client_id_to_stop_event[self.next_client_id] = threading.Event()
        self.client_id_to_handler_thread[self.next_client_id] = threading.Thread(
            target=self.__client_handler,
            args=(self.next_client_id,)
        )

        # Default client information

        self.client_id_to_name[self.next_client_id] = f"Player {self.next_client_id}"

        # Start the handler thread

        self.client_id_to_handler_thread[self.next_client_id].start()

        # For the next client

        self.next_client_id += 1

    def __accept_clients(self) -> None:
        while not self.accept_clients_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if readable:
                client_socket, client_address = self.socket.accept()

                self.setup_client_from_socket_address(client_socket, client_address)

    def start_accepting_clients(self) -> None:
        if self.accept_clients_thread is not None:
            return

        self.print(f"Server : Start accepting new clients")

        self.accept_clients_stop_event.clear()

        self.accept_clients_thread = threading.Thread(
            target=self.__accept_clients
        )
        self.accept_clients_thread.start()

    def stop_accepting_clients(self):
        if self.accept_clients_thread is None:
            return

        self.print(f"Server : Stop accepting new clients")

        self.accept_clients_stop_event.set()
        self.accept_clients_thread.join()
        self.accept_clients_thread = None

    def __client_handshake(self, client_id: int, client_socket: socket.socket) -> bool:
        """
        Perform a handshake between client and server.
        The type of connection request is extracted and, if correct, the clients id sent.

        :param client_id: The client id of the client to handshake.
        :param client_socket: The socket of the client to handshake.
        :return: True if handshake was successful, False otherwise.
        """

        self.print(f"Client ID {client_id: 3} : Performing handshake")

        # Receive a new connection request from the client
        indicator_bytes = client_socket.recv(IndicatorByte.size_in_bytes)
        indicator_int = struct.unpack(IndicatorByte.format_string, indicator_bytes)[0]

        if indicator_int != ClientMessageInfo.NEW_CONNECTION_REQUEST.value:
            self.print(f"Client ID {client_id: 3} :Handshake failed")
            # Crash and burn
            return False

        # Send the client its client id
        client_socket.sendall(
            ServerMessageInfo.CLIENT_SET_ID.create_bytes(client_id)
        )

        # Handshake successful
        self.print(f"Client ID {client_id: 3} : Handshake succeeded")
        return True

    def __handle_client_name_change(self, client_id: int, client_socket: socket.socket) -> bool:
        """
        Handles the client requesting a name change.

        :param client_id: The id of the client requesting a name change.
        :param client_socket: The socket of the client requesting a name change.
        :return: True if successful and the clients name was updated, false otherwise.
        """

        self.print(f"Client ID {client_id: 3} : Handling name change")

        # Acquire the length of the string
        name_change_length_bytes = client_socket.recv(
            ClientMessageInfo.NAME_CHANGE_HEADER.size_in_bytes
        )
        name_change_length, = struct.unpack(
            ClientMessageInfo.NAME_CHANGE_HEADER.format_string,
            name_change_length_bytes
        )

        # Read all the string bytes
        name_bytes: bytearray = bytearray()
        while (num_bytes_received := len(name_bytes)) < name_change_length:
            name_bytes.extend(
                client_socket.recv(name_change_length - num_bytes_received)
            )

        # Attempt conversion
        try:
            name_string = name_bytes.decode("UTF-8")
        except UnicodeDecodeError:
            # Error, so tell rejected
            client_socket.sendall(
                ServerMessageInfo.CLIENT_NAME_REJECTED.create_bytes()
            )

            self.print(f"Client ID {client_id: 3} : Name rejected")

            return False

        # Done, so tell accepted
        self.client_id_to_name[client_id] = name_string
        client_socket.sendall(
            ServerMessageInfo.CLIENT_NAME_ACCEPTED.create_bytes()
        )

        self.print(f"Client ID {client_id: 3} : Name accepted")

        return True

    def __client_handler(self, client_id: int) -> None:
        """
        Completes the handshake between client and server.
        Then runs a loop handling the information being sent from the client to the server.
        If the handshake was unsuccessful, the information regarding the client is deleted.

        :param client_id: The client id of the client being handled.
        """

        self.print(f"Client ID {client_id: 3} : Starting client handler")

        client_socket = self.client_id_to_socket[client_id]

        handshake_result = self.__client_handshake(client_id, client_socket)

        if not handshake_result:
            self.print(f"Client ID {client_id: 3} : Closing socket")
            client_socket.close()
            self.delete_information_regarding_client_id(client_id)
            return

        self.client_updater_task_queue.put(
            (_ServerTasks.INFORM_CLIENT_CONNECTED, (client_id,))
        )

        stop_event = self.client_id_to_stop_event[client_id]

        while not stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if not readable:
                continue

            indicator_byte = client_socket.recv(1)
            indicator_int, = struct.unpack(IndicatorByte.format_string, indicator_byte)

            if indicator_int == ClientMessageInfo.NAME_CHANGE_HEADER.value:
                name_change_result = self.__handle_client_name_change(client_id, client_socket)

                if name_change_result:
                    self.client_updater_task_queue.put(
                        (_ServerTasks.INFORM_CLIENT_NAME, (client_id, self.client_id_to_name[client_id]))
                    )

            else:
                # Invalid indicator integer
                pass

        self.print(f"Client ID {client_id: 3} : Consumer loop exited")

        self.print(f"Client ID {client_id: 3} : Closing socket")
        client_socket.close()
        self.delete_information_regarding_client_id(client_id)

    def __client_updater(self) -> None:
        """
        Consumes tasks from the client updater task queue and reflects the updates to each client.
        """

        while not self.client_updater_stop_event.is_set():
            try:
                task, info = self.client_updater_task_queue.get(timeout=0.1)

            except queue.Empty:
                continue

            self.print(f"Client Updater : Received task {task.name}")

            to_send: bytes

            if task == _ServerTasks.INFORM_CLIENT_CONNECTED:
                to_send = ServerMessageInfo.CLIENT_CONNECTED_NOTIFICATION.create_bytes(info[0])

            elif task == _ServerTasks.INFORM_CLIENT_NAME:
                name_bytes = info[1].encode("UTF-8")
                to_send = ServerMessageInfo.CLIENT_NEW_NAME_HEADER.create_bytes(info[0], len(name_bytes))
                to_send += name_bytes

            elif task == _ServerTasks.INFORM_CLIENT_DISCONNECTED:
                to_send = ServerMessageInfo.CLIENT_DISCONNECTED_NOTIFICATION.create_bytes(info[0])

            else:
                continue

            self.print(f"Client Updater : Sending bytes {to_send}")

            for client_socket in self.client_id_to_socket.values():
                client_socket.sendall(to_send)

    def start_client_updater(self) -> None:
        """
        Starts the underlying client updater thread if it is not running.
        """

        if self.client_updater_thread is not None:
            return

        self.print(f"Server : Starting client updater")

        self.client_updater_stop_event.clear()

        self.client_updater_thread = threading.Thread(
            target=self.__client_updater
        )
        self.client_updater_thread.start()

    def stop_client_updater(self) -> None:
        """
        Stops the underlying client updater thread if it is running.
        Does not check if the task queue is empty.
        There may be unfinished tasks.
        """

        if self.client_updater_thread is None:
            return

        self.print(f"Server : Stopping client updater")

        self.client_updater_stop_event.set()
        self.client_updater_thread.join()
        self.client_updater_thread = None

    def set_all_client_stop_events(self) -> None:
        self.print(f"Server : Setting all client stop events")

        for stop_event in self.client_id_to_stop_event.values():
            stop_event.set()

    def join_all_client_handler_threads(self) -> None:
        self.print(f"Server : Joining all client handler threads")

        for handler_thread in self.client_id_to_handler_thread.values():
            handler_thread.join()

    def close_all_client_sockets(self) -> None:
        self.print(f"Server : Closing all client sockets")

        for client_socket in self.client_id_to_socket.values():
            client_socket.close()


def main():
    from get_my_ip import get_my_ip

    server = Server(get_my_ip(), 8888)
    server.start_accepting_clients()
    server.start_client_updater()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        pass

    server.stop_accepting_clients()
    server.stop_client_updater()

    server.set_all_client_stop_events()
    server.join_all_client_handler_threads()
    server.close_all_client_sockets()

    print("Closing server socket")
    server.socket.close()


if __name__ == "__main__":
    main()
