import socket
import struct
import threading
from ipaddress import IPv4Address

import select

from MessageTypeIndicators import ClientMessageInfo, IndicatorByte, ServerMessageInfo


class Client:
    def __init__(self):
        self.server_ip: IPv4Address | None = None
        self.server_port: int | None = None

        self.socket: socket.socket | None = None

        self.client_id: int = 0

        self.information_receiver_stop_event: threading.Event = threading.Event()
        self.information_receiver_thread: threading.Thread | None = None

        self.other_client_id_to_name: dict[int, str] = {}

    def __handle_new_client_connected(self) -> None:
        """
        Handles updating the internal information for when a new client connects to the server.
        """

        # Acquire the client id of the newly connected client
        client_id_bytes = self.socket.recv(
            ServerMessageInfo.CLIENT_CONNECTED_NOTIFICATION.size_in_bytes
        )
        other_client_id, = struct.unpack(
            ServerMessageInfo.CLIENT_CONNECTED_NOTIFICATION.format_string,
            client_id_bytes
        )

        # Save it
        self.other_client_id_to_name[other_client_id] = f"Player {other_client_id}"

    def __handle_other_client_disconnected(self) -> None:
        """
        Handles updating the internal information for when a client disconnects from the server.
        """

        # Acquire the client id of the disconnected client
        client_id_bytes = self.socket.recv(
            ServerMessageInfo.CLIENT_CONNECTED_NOTIFICATION.size_in_bytes
        )
        other_client_id, = struct.unpack(
            ServerMessageInfo.CLIENT_CONNECTED_NOTIFICATION.format_string,
            client_id_bytes
        )

        # Yeet
        del self.other_client_id_to_name[other_client_id]

    def __handle_other_client_name_change(self) -> None:
        """
        Handles updating the internal information for when another client changes its name.
        """

        # Acquire the client id and the length of the string
        other_client_id_name_length_bytes = self.socket.recv(
            ServerMessageInfo.CLIENT_NEW_NAME_HEADER.size_in_bytes
        )
        other_client_id, name_length = struct.unpack(
            ServerMessageInfo.CLIENT_NEW_NAME_HEADER.format_string,
            other_client_id_name_length_bytes
        )

        # Read all the string bytes
        name_bytes: bytearray = bytearray()
        while (num_bytes_received := len(name_bytes)) < name_length:
            name_bytes.extend(
                self.socket.recv(name_length - num_bytes_received)
            )

        # Assume the conversion works as the server already checks this
        name_string = name_bytes.decode("UTF-8")

        # Save
        self.other_client_id_to_name[other_client_id] = name_string

    def __information_receiver(self) -> None:
        """
        Runs a loop handling the information being sent from the server to this client.
        """

        while not self.information_receiver_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if not readable:
                continue

            indicator_byte = self.socket.recv(1)
            indicator_int, = struct.unpack(IndicatorByte.format_string, indicator_byte)

            if indicator_int == ServerMessageInfo.CLIENT_CONNECTED_NOTIFICATION.value:
                self.__handle_new_client_connected()

            elif indicator_int == ServerMessageInfo.CLIENT_DISCONNECTED_NOTIFICATION.value:
                self.__handle_other_client_disconnected()

            elif indicator_int == ServerMessageInfo.CLIENT_NEW_NAME_HEADER:
                self.__handle_other_client_name_change()

            else:
                pass

    def start_information_receiver(self) -> None:
        if self.information_receiver_thread is not None:
            return

        self.information_receiver_stop_event.clear()

        self.information_receiver_thread = threading.Thread(
            target=self.__information_receiver
        )
        self.information_receiver_thread.start()

    def stop_information_receiver(self) -> None:
        if self.information_receiver_thread is None:
            return

        self.information_receiver_stop_event.set()
        self.information_receiver_thread.join()
        self.information_receiver_thread = None

    def connect_to_server(self, server_ip: IPv4Address, server_port: int) -> bool:
        self.socket = socket.socket()

        try:
            self.socket.connect((str(server_ip), server_port))
        except (ConnectionResetError, TimeoutError):
            self.socket = None
            return False

        self.socket.sendall(ClientMessageInfo.NEW_CONNECTION_REQUEST.create_bytes())

        indicator_bytes = self.socket.recv(IndicatorByte.size_in_bytes)
        indicator_int = struct.unpack(IndicatorByte.format_string, indicator_bytes)[0]

        if indicator_int != ServerMessageInfo.CLIENT_SET_ID.value:
            self.socket.close()

        self.start_information_receiver()

        return True

    def disconnect_from_server(self) -> None:
        self.stop_information_receiver()


def main():
    from get_my_ip import get_my_ip

    client = Client()
    connect_result = client.connect_to_server(get_my_ip(), 8888)

    if not connect_result:
        print("Failed to connect to the server")
        return

    try:
        while True:
            pass

    except KeyboardInterrupt:
        pass

    client.disconnect_from_server()


if __name__ == "__main__":
    main()
