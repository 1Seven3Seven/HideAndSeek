import socket
import struct
import threading
from ipaddress import IPv4Address

import select

from Utils import *

client_id_list: list[int] = []


def server_update_handler(soc: socket.socket, stop_event: threading.Event):
    global client_id_list

    Logger.log("Thread started")

    while not stop_event.is_set():
        readable, _, _ = select.select([soc], [], [], 0.1)

        if not readable:
            continue

        Logger.log("Reading indicator int from socket")
        try:
            indicator_int = IndicatorInt.read_from_socket(soc)
        except struct.error:
            Logger.log("Error unpacking struct, closing socket")
            soc.close()
            break

        if indicator_int != ServerMessageInfo.CONNECTED_CLIENT_IDS_HEADER.value:
            Logger.log(f"Incorrect indicator int {hex(indicator_int)}, closing socket")
            soc.close()
            break

        Logger.log("Reading the number of client ids from the socket")
        connected_client_ids_len_bytes = soc.recv(ServerMessageInfo.CONNECTED_CLIENT_IDS_HEADER.size_in_bytes)
        try:
            connected_client_ids_len, = struct.unpack(
                ServerMessageInfo.CONNECTED_CLIENT_IDS_HEADER.format_string,
                connected_client_ids_len_bytes
            )
        except struct.error:
            Logger.log("Error unpacking bytes, closing socket")
            soc.close()
            break

        format_str = "I" * connected_client_ids_len

        connected_client_ids_bytes = soc.recv(
            struct.calcsize(format_str)
        )
        try:
            connected_client_ids = struct.unpack(format_str, connected_client_ids_bytes)
        except struct.error:
            Logger.log("Error unpacking bytes, closing socket")
            soc.close()
            break

        client_id_list = list(connected_client_ids)

        Logger.log(f"Client id list is now {client_id_list}")

    Logger.log("Thread exiting")


def connect(ip: IPv4Address, port: int) -> tuple[socket.socket, int] | None:
    Logger.log(f"Attempting connection to server at address {ip}:{port}")
    soc = socket.socket()
    soc.settimeout(2)
    try:
        soc.connect((str(ip), port))
    except TimeoutError:
        Logger.log("Connection attempt timed out")
        return None
    Logger.log("Connection successful")
    soc.settimeout(None)

    Logger.log("Sending new connection request")
    soc.sendall(
        ClientMessageInfo.NEW_CONNECTION_REQUEST.create_bytes()
    )

    Logger.log("Reading indicator int")
    try:
        indicator_int = IndicatorInt.read_from_socket(soc)
    except (OSError, struct.error) as e:
        Logger.log(f"Received error '{e}', closing socket")
        soc.close()
        return None

    if indicator_int != ServerMessageInfo.CLIENT_ID.value:
        Logger.log(f"Incorrect indicator int {hex(indicator_int)}, closing socket")
        soc.close()
        return None

    Logger.log("Reading client id")
    try:
        client_id_bytes = soc.recv(ServerMessageInfo.CLIENT_ID.size_in_bytes)
    except OSError as e:
        Logger.log(f"Received error '{e}', closing socket")
        soc.close()
        return None

    try:
        client_id, = struct.unpack(
            ServerMessageInfo.CLIENT_ID.format_string, client_id_bytes
        )
    except struct.error as e:
        Logger.log(f"Received error '{e}', closing socket")
        soc.close()
        return None

    Logger.log(f"Received client id {client_id}")

    return soc, client_id


def main(ip: IPv4Address, port: int) -> None:
    result = connect(ip, port)

    if result is None:
        Logger.log("Error connecting to server")
        return

    soc, client_id = result

    Logger.log("Starting server update handler thread")
    server_update_handler_stop_event = threading.Event()
    server_update_handler_thread = threading.Thread(
        target=server_update_handler,
        args=(soc, server_update_handler_stop_event)
    )
    server_update_handler_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    Logger.log("Notifying server of disconnect")
    soc.sendall(
        ClientMessageInfo.WILL_DISCONNECT.create_bytes()
    )

    # Cleanup
    Logger.log("Setting server update handler stop event")
    server_update_handler_stop_event.set()
    Logger.log("Joining server update handler thread")
    server_update_handler_thread.join()

    Logger.log("Closing client socket")
    soc.close()

    Logger.log("All done")


if __name__ == "__main__":
    main(get_my_ip(), 8888)
    # main("localhost", 8888)
