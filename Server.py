import socket
import struct
import threading
from ipaddress import IPv4Address

import select

from ClientHandlerManager import ClientHandlerManager
from Utils import *


def accept_new_clients(soc: socket.socket, stop_event: threading.Event,
                       client_handler_manager: ClientHandlerManager) -> None:
    next_client_id = 1

    Logger.log("Thread started")

    while not stop_event.is_set():
        readable, _, _ = select.select([soc], [], [], 0.1)

        if not readable:
            continue

        client_socket, client_address = soc.accept()
        Logger.log(f"Client under address {client_address[0]}:{client_address[1]} requested connection")

        Logger.log("Reading indicator int from socket")
        try:
            indicator_int = IndicatorInt.read_from_socket(client_socket)
        except struct.error:
            Logger.log("Error unpacking struct, closing socket")
            client_socket.close()
            continue

        if indicator_int != ClientMessageInfo.NEW_CONNECTION_REQUEST.value:
            Logger.log(f"Incorrect indicator int {indicator_int}, closing socket")
            client_socket.close()
            continue

        Logger.log("Correct indicator int")

        Logger.log(f"Sending client id {next_client_id} to client")
        try:
            client_socket.sendall(
                ServerMessageInfo.CLIENT_ID.create_bytes(next_client_id)
            )
        except OSError as e:
            Logger.log(f"Received error '{e}'")

        client_handler_manager.handle_client(next_client_id, client_socket, client_address)

        next_client_id += 1

        Logger.log("Adding notify task")


def main(ip: IPv4Address, port: int) -> None:
    Logger.log(f"Binding socket to {ip}:{port}")
    soc = socket.socket()
    soc.bind((str(ip), port))

    Logger.log("Listening for client connections")
    soc.listen()

    # Setting up the client handler manager
    client_handler_manager = ClientHandlerManager()
    client_handler_manager.start()

    # Setting up the accept new clients thread

    accept_new_clients_stop_event: threading.Event = threading.Event()

    accept_new_clients_thread = threading.Thread(
        target=accept_new_clients,
        args=(soc, accept_new_clients_stop_event, client_handler_manager)
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

    Logger.log("Closing server socket")
    soc.close()

    Logger.log("Shutting down client handler manager")
    client_handler_manager.shutdown()

    Logger.log("All done")


if __name__ == "__main__":
    main(get_my_ip(), 8888)
    # main("localhost", 8888)
