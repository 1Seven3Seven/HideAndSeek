import socket
import struct

from Utils import ClientMessageInfo as ClientMI
from Utils import IndicatorByte, get_my_ip
from Utils import ServerMessageInfo as ServerMI


def main() -> None:
    print(f"Connecting to server")
    client_socket = socket.socket()
    client_socket.settimeout(2)
    try:
        client_socket.connect((str(get_my_ip()), 8888))
    except TimeoutError:
        print("Connection request timed out")
        print("Closing socket")
        client_socket.close()
        return

    print("Connected, sending connection request")
    to_send_bytes = ClientMI.NEW_CONNECTION_REQUEST.create_bytes()
    print(f"\tSending bytes {to_send_bytes}")
    try:
        client_socket.sendall(to_send_bytes)
    except OSError:
        print("Error with the connection")
        print("Closing socket")
        client_socket.close()
        return

    print("Waiting for indicator")
    try:
        indicator_byte = client_socket.recv(
            IndicatorByte.size_in_bytes
        )
    except TimeoutError:
        print("Connection request timed out")
        print("Closing socket")
        client_socket.close()
        return

    print(f"\tReceived bytes {indicator_byte}")
    try:
        indicator_int, = struct.unpack(
            IndicatorByte.format_string,
            indicator_byte
        )
    except struct.error as e:
        print(f"When attempting to unpack received error {e}")
        print("Closing socket")
        client_socket.close()
        return

    print(f"Received indicator int {indicator_int}")

    if indicator_int != ServerMI.CLIENT_SET_ID.value:
        print("Incorrect indicator int, closing socket")
        print("Closing socket")
        client_socket.close()
        return

    print("Correct indicator int, reading client id")
    try:
        client_id_bytes = client_socket.recv(
            ServerMI.CLIENT_SET_ID.size_in_bytes
        )
    except TimeoutError:
        print("Connection request timed out")
        print("Closing socket")
        client_socket.close()
        return

    print(f"\tReceived bytes {client_id_bytes}")
    try:
        client_id, = struct.unpack(
            ServerMI.CLIENT_SET_ID.format_string,
            client_id_bytes
        )
    except struct.error as e:
        print(f"When attempting to unpack received error {e}")
        print("Closing socket")
        client_socket.close()
        return

    print(f"Received client id {client_id}")

    print("Closing socket")
    client_socket.close()

    print("All done")


if __name__ == "__main__":
    main()
