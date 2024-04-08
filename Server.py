import queue
import socket
import struct
import threading
from ipaddress import IPv4Address
from typing import Literal

import select

from ClientHandler import ClientHandler
from Utils import *

Tasks = Literal["New Client Connected"]

modify_lock: threading.Lock = threading.Lock()

client_id_to_handler: dict[int, ClientHandler] = {}
next_client_id = 1


def client_updater(task_queue: queue.Queue[Tasks], stop_event: threading.Event) -> None:
    _prepend = "CU:"

    Logger.log(_prepend, "Thread started")

    while not stop_event.is_set():
        try:
            task = task_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        Logger.log(_prepend, f"Received task '{task}'")

        if task == "New Client Connected":
            Logger.log(_prepend, "Grabbing current client list")
            with modify_lock:
                client_id_tuple = tuple(client_id_to_handler.keys())
                client_handler_tuple = tuple(client_id_to_handler.values())

            len_client_id_tuple = len(client_id_tuple)

            Logger.log(_prepend, "Creating bytes to send")
            header_bytes_to_send = ServerMessageInfo.CONNECTED_CLIENT_IDS.create_bytes(
                len_client_id_tuple
            )

            body_bytes_to_send = struct.pack(
                "I" * len_client_id_tuple,
                *client_id_tuple
            )

            bytes_to_send = header_bytes_to_send + body_bytes_to_send

            Logger.log(_prepend, "Sending bytes")
            need_to_re_update = False

            client_handler: ClientHandler
            client_id: int
            for client_handler, client_id in zip(client_handler_tuple, client_id_tuple):
                try:
                    client_handler.socket.sendall(bytes_to_send)
                except OSError as e:
                    Logger.log(_prepend, f"When sending to client id {client_id}, received error '{e}'")
                    Logger.log(_prepend, "Closing socket and removing client")
                    client_handler.socket.close()
                    with modify_lock:
                        del client_id_to_handler[client_id]

            if need_to_re_update:
                task_queue.put("New Client Connected")

        else:
            Logger.log(_prepend, f"Unknown task")


def accept_new_clients(soc: socket.socket, stop_event: threading.Event, task_queue: queue.Queue[Tasks]) -> None:
    global next_client_id

    _prepend = "ANC:"

    Logger.log(_prepend, "Thread started")

    while not stop_event.is_set():
        readable, _, _ = select.select([soc], [], [], 0.1)

        if not readable:
            continue

        client_socket, client_address = soc.accept()
        Logger.log(_prepend, f"Client under address {client_address[0]}:{client_address[1]} requested connection")

        Logger.log(_prepend, "Reading indicator int from socket")
        try:
            indicator_int = IndicatorInt.read_from_socket(client_socket)
        except struct.error:
            Logger.log(_prepend, "Error unpacking struct, closing socket")
            client_socket.close()
            continue

        if indicator_int != ClientMessageInfo.NEW_CONNECTION_REQUEST.value:
            Logger.log(_prepend, f"Incorrect indicator int {indicator_int}, closing socket")
            client_socket.close()
            continue

        Logger.log(_prepend, "Correct indicator int")

        with modify_lock:
            Logger.log(_prepend, f"Client id is {next_client_id}")
            client_id_to_handler[next_client_id] = ClientHandler(next_client_id, client_socket, client_address)

        Logger.log(_prepend, "Sending client id to client")
        client_socket.sendall(
            ServerMessageInfo.CLIENT_ID.create_bytes(next_client_id)
        )

        next_client_id += 1

        Logger.log(_prepend, "Adding notify task")
        task_queue.put("New Client Connected")


def main(ip: IPv4Address, port: int) -> None:
    Logger.log(f"Binding socket to {ip}:{port}")
    soc = socket.socket()
    soc.bind((str(ip), port))

    Logger.log("Listening for client connections")
    soc.listen()

    # Setting up the client updater thread

    client_updater_task_queue: queue.Queue[Tasks] = queue.Queue()
    client_updater_stop_event = threading.Event()

    client_updater_thread = threading.Thread(
        target=client_updater,
        args=(client_updater_task_queue, client_updater_stop_event)
    )
    client_updater_thread.start()

    # Setting up the accept new clients thread

    accept_new_clients_stop_event: threading.Event = threading.Event()

    accept_new_clients_thread = threading.Thread(
        target=accept_new_clients,
        args=(soc, accept_new_clients_stop_event, client_updater_task_queue)
    )
    accept_new_clients_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    # Cleanup
    Logger.log("Setting accept new clients stop event")
    accept_new_clients_stop_event.set()
    Logger.log("Joining accept new clients thread")
    accept_new_clients_thread.join()

    Logger.log("Setting client updater stop event")
    client_updater_stop_event.set()
    Logger.log("Joining client updater thread")
    client_updater_thread.join()

    Logger.log("Closing server socket")
    soc.close()

    Logger.log("All done")


if __name__ == "__main__":
    main(get_my_ip(), 8888)
    # main("localhost", 8888)
