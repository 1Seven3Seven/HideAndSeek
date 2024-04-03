import socket
import threading

import select

from ClientHandler import ClientHandler
from Logger import Logger
from Utils import get_my_ip

next_client_id = 1

client_id_to_client_handler: dict[int, ClientHandler] = {}


def accept_new_clients(server_socket: socket.socket, stop_event: threading.Event):
    global next_client_id

    Logger.log("Accept Thread : Started")

    server_socket.listen()

    while not stop_event.is_set():
        readable, _, _ = select.select([server_socket], [], [], 0.1)

        if not readable:
            continue

        client_socket, client_address = server_socket.accept()

        Logger.log(f"Accept Thread : Accepted client from address {client_address} with client id {next_client_id}")

        client_handler = ClientHandler(client_socket, client_address, next_client_id)
        client_id_to_client_handler[next_client_id] = client_handler
        client_handler.start()

        next_client_id += 1

    Logger.log("Accept Thread : Stop event set, all finished")


def main() -> None:
    Logger.log("Server : Creating and binding socket")
    server_socket = socket.socket()
    server_socket.settimeout(2)
    server_socket.bind((str(get_my_ip()), 8888))

    Logger.log("Server : Setting up accepting thread")
    accept_new_clients_stop_event = threading.Event()
    accept_new_clients_thread = threading.Thread(
        target=accept_new_clients,
        args=(server_socket, accept_new_clients_stop_event)
    )
    accept_new_clients_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    Logger.log("Server : Setting stop event")
    accept_new_clients_stop_event.set()
    Logger.log("Server : Waiting for accept thread to finish")
    accept_new_clients_thread.join()

    Logger.log("Server : Closing server socket")
    server_socket.close()

    Logger.log("Server : Joining all handler threads")
    for client_handler in client_id_to_client_handler.values():
        client_handler.handle_client_thread.join()

    Logger.log("Server : All done")


if __name__ == "__main__":
    main()
