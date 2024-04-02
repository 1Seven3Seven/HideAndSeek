import socket
import struct
import threading

import select

from Utils import ClientMessageInfo as ClientMI
from Utils import IndicatorByte, get_my_ip
from Utils import ServerMessageInfo as ServerMI

next_client_id = 1

client_id_to_socket: dict[int, socket.socket] = {}
client_id_to_address: dict[int, tuple[str, int]] = {}
client_id_to_handshake_thread: dict[int, threading.Thread] = {}

neatness_lock: threading.Lock = threading.Lock()


def log(*_args, **_kwargs) -> None:
    with neatness_lock:
        print(*_args, **_kwargs)


def handshake(client_socket: socket.socket, client_id: int) -> None:
    """
    Performs the initial handshake with the client given its socket and id.

    :param client_socket: The socket for the client.
    :param client_id: The id for the client.
    """

    log(f"Client {client_id: 3} : Performing handshake")

    log(f"Client {client_id: 3} : Waiting for indicator")
    try:
        indicator_byte = client_socket.recv(
            IndicatorByte.size_in_bytes
        )
    except TimeoutError:
        log(f"Client {client_id: 3} : Connection request timed out")
        log(f"Client {client_id: 3} : Closing socket")
        client_socket.close()
        return

    log(f"Client {client_id: 3} :     Received bytes {indicator_byte}")
    try:
        indicator_int, = struct.unpack(
            IndicatorByte.format_string,
            indicator_byte
        )
    except struct.error as e:
        log(f"Client {client_id: 3} : When attempting to unpack received error {e}")
        log(f"Client {client_id: 3} : Closing socket")
        client_socket.close()
        return

    log(f"Client {client_id: 3} : Received indicator int {indicator_int}")

    if indicator_int != ClientMI.NEW_CONNECTION_REQUEST.value:
        log(f"Client {client_id: 3} : Incorrect indicator int")
        log(f"Client {client_id: 3} : Closing socket")
        client_socket.close()
        return

    log(f"Client {client_id: 3} : Correct indicator int")

    log(f"Client {client_id: 3} : Sending client id")
    to_send_bytes = ServerMI.CLIENT_SET_ID.create_bytes(client_id)
    log(f"Client {client_id: 3} :     Sending bytes {to_send_bytes}")
    try:
        client_socket.sendall(to_send_bytes)
    except OSError:
        log(f"Client {client_id: 3} : Error with the connection")
        log(f"Client {client_id: 3} : Closing socket")
        client_socket.close()
        return

    log(f"Client {client_id: 3} : All done")
    log(f"Client {client_id: 3} : Closing socket")
    client_socket.close()
    return


def accept_new_clients(server_socket: socket.socket, stop_event: threading.Event):
    global next_client_id

    log(f"Accept Thread : Started")

    server_socket.listen()

    while not stop_event.is_set():
        readable, _, _ = select.select([server_socket], [], [], 0.1)

        if not readable:
            continue

        client_socket, client_address = server_socket.accept()

        log(f"Accept Thread : Accepted client from address {client_address} with client id {next_client_id}")

        client_id_to_socket[next_client_id] = client_socket
        client_id_to_address[next_client_id] = client_address

        client_id_to_handshake_thread[next_client_id] = threading.Thread(
            target=handshake,
            args=(client_socket, next_client_id)
        )
        client_id_to_handshake_thread[next_client_id].start()

        next_client_id += 1

    log(f"Accept Thread : Stop event set, all finished")


def main() -> None:
    log(f"Server : Creating and binding socket")
    server_socket = socket.socket()
    server_socket.settimeout(2)
    server_socket.bind((str(get_my_ip()), 8888))

    log(f"Server : Setting up accepting thread")
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

    log(f"Server : Setting stop event")
    accept_new_clients_stop_event.set()
    log(f"Server : Waiting for accept thread to finish")
    accept_new_clients_thread.join()

    log(f"Server : Closing server socket")
    server_socket.close()

    log(f"Server : Joining all handshake threads")
    for thread in client_id_to_handshake_thread.values():
        thread.join()

    log(f"Server : All done")


if __name__ == "__main__":
    main()
