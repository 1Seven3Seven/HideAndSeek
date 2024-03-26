import socket
import threading
from ipaddress import IPv4Address

import pygame.time
import select

from get_my_ip import get_my_ip

ENCODING = "UTF-8"


class Server:
    def __init__(self, my_ip: IPv4Address, port: int):
        self.ip: IPv4Address = my_ip
        self.port: int = port

        self.socket: socket.socket = socket.socket()
        self.socket.bind((str(self.ip), self.port))

        self._accept_new_clients_stop_event: threading.Event = threading.Event()
        self._accept_new_clients_thread: threading.Thread | None = None

        self.__next_client_id: int = 0
        """
        The id for the next client to be accepted, must be incremented after use.
        Should only be interacted with by the thread responsible for accepting new client requests.
        """
        self.client_id_to_socket: dict[int, socket.socket] = {}
        self.client_id_to_address: dict[int, tuple[str, int]] = {}
        self.client_id_to_handler_stop_event: dict[int, threading.Event] = {}
        self.client_id_to_handler_thread: dict[int, threading.Thread] = {}
        self.client_id_to_position: dict[int, tuple[int, int]] = {}
        self.client_id_to_enemy_position: dict[int, list[int, int]] = {}

    def __accept_new_clients(self) -> None:
        """
        Accepts new client connections and establishes a thread to handle them.
        """

        while not self._accept_new_clients_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if readable:
                client_socket, client_address = self.socket.accept()

                self.client_id_to_socket[self.__next_client_id] = client_socket
                self.client_id_to_address[self.__next_client_id] = client_address

                self.client_id_to_handler_stop_event[self.__next_client_id] = threading.Event()

                self.client_id_to_handler_thread[self.__next_client_id] = threading.Thread(
                    target=self.__handle_client,
                    args=(self.__next_client_id,),
                    name=f"Server.__handle_client for client at address {client_address[0]}:{client_address[1]}"
                )
                self.client_id_to_handler_thread[self.__next_client_id].start()

                self.__next_client_id += 1

    def start_accepting_new_clients(self) -> None:
        if self._accept_new_clients_thread is not None:
            return

        self.socket.listen()

        self._accept_new_clients_thread = threading.Thread(
            target=self.__accept_new_clients,
            name=f"Server.__accept_new_clients"
        )
        self._accept_new_clients_thread.start()

    def stop_accepting_new_clients(self) -> None:
        if self._accept_new_clients_thread is None:
            return

        self._accept_new_clients_stop_event.set()
        self._accept_new_clients_thread.join()

    def __remove_client_data(self, client_id: int) -> None:
        """
        Removes all data associated with the given client id.
        :param client_id: The client id whose data should be removed.
        """

        if client_id in self.client_id_to_socket:
            del self.client_id_to_socket[client_id]

        if client_id in self.client_id_to_address:
            del self.client_id_to_address[client_id]

        if client_id in self.client_id_to_handler_stop_event:
            del self.client_id_to_handler_stop_event[client_id]

        if client_id in self.client_id_to_handler_thread:
            del self.client_id_to_handler_thread[client_id]

        if client_id in self.client_id_to_position:
            del self.client_id_to_position[client_id]

    def __handle_client(self, client_id: int) -> None:
        """
        Handles the client for the given id by performing the handshake then updating its position.
        Finally, handles the termination of the connection.
        :param client_id: The id of the client to be handled.
        """

        # Grabbing socket for ease of use
        client_socket: socket.socket = self.client_id_to_socket[client_id]

        # region - Acquiring the initial client position

        initial_position_str = client_socket.recv(1024).decode(ENCODING)
        # "initial_position:xxx,yyy|"
        if not (initial_position_str.startswith("initial_position:") and initial_position_str.endswith("|")):
            # Fatal error
            client_socket.close()
            self.__remove_client_data(client_id)
            return

        # "initial_position:xxx,yyy|"
        initial_position_str = initial_position_str.split(":")[1]
        # "xxx,yyy|"
        initial_position_str = initial_position_str[:-1]
        # "xxx,yyy"
        initial_x_str, initial_y_str = initial_position_str.split(",")
        # "xxx", "yyy"

        self.client_id_to_position[client_id] = (int(initial_x_str), int(initial_y_str))
        self.client_id_to_enemy_position[client_id] = [int(initial_x_str), int(initial_y_str)]

        # endregion

        # Sending the client its id

        client_socket.sendall(f"{client_id}|".encode(ENCODING))

        # region - Making sure the client has received the correct id

        client_id_response_str = client_socket.recv(1024).decode(ENCODING)
        # "id|"
        if not client_id_response_str.endswith("|"):
            # Fatal error
            client_socket.close()
            self.__remove_client_data(client_id)
            return

        # "id|"
        client_id_response_str = client_id_response_str[:-1]
        # "id"
        if not client_id == int(client_id_response_str):
            # Fatal error
            client_socket.close()
            self.__remove_client_data(client_id)
            return

        # endregion

        # Received id is correct, now to start

        client_socket.sendall("start|".encode(ENCODING))

        # Loop to constantly update the client position

        # Grab the stop event for ease of use
        stop_event = self.client_id_to_handler_stop_event[client_id]

        while not stop_event.is_set():
            readable, _, _ = select.select([client_socket], [], [], 0.1)

            if not readable:
                continue

            client_position_info_str = client_socket.recv(1024).decode(ENCODING)

            # Two cases, split on "|:
            # "xxx,yyy|xxx,yyy|"  -> ["xxx,yyy", "xxx,yyy", ""]
            # "xxx,yyy|terminate" -> ["xxx,yyy", "terminate"]

            client_position_info = client_position_info_str.split("|")
            if client_position_info[-1] == "terminate":
                break

            x_str, y_str = client_position_info[-2].split(",")
            self.client_id_to_position[client_id] = (int(x_str), int(y_str))

        # If we are out of the update loop then either the client or the server issued a termination
        # If the stop event is set, then the server initiated the termination

        if stop_event.is_set():
            # Server issued the termination, wait for the client to send the response

            # Reset the stop event, the server can set this again to force exit
            stop_event.set()
            while not stop_event.is_set():
                readable, _, _ = select.select([client_socket], [], [], 0.1)

                if readable:
                    client_terminate_response_str = client_socket.recv(1024).decode(ENCODING)
                    # Make sure that there are no positions tacked on
                    client_terminate_response_str = client_terminate_response_str.split("|")[-1]

                    if client_terminate_response_str == "terminate":
                        break

        else:
            # Client issued the termination
            # Send the response
            client_socket.sendall("terminate".encode(ENCODING))
            # Done

        # Socket closed
        client_socket.close()
        # Delete the information
        self.__remove_client_data(client_id)

    def create_client_position_information_string(self) -> str:
        """
        Creates the string containing the enemy position and the target position for each client.
        :return: The position information string.
        """

        client_information: list[str] = []

        for client_id, client_position in self.client_id_to_position.items():
            enemy_pos = self.client_id_to_enemy_position[client_id]
            temp_str = f"{client_id};{client_position[0]},{client_position[1]};{enemy_pos[0]},{enemy_pos[1]}"
            client_information.append(temp_str)

        position_information_string = ":".join(client_information)
        position_information_string += "|"

        return position_information_string

    def send_position_information_to_each_client(self) -> None:
        position_information_string = self.create_client_position_information_string()
        position_information_bytes = position_information_string.encode(ENCODING)

        for client_socket in self.client_id_to_socket.values():
            client_socket.sendall(position_information_bytes)

    def update_enemy_positions(self) -> None:
        for client_id, client_position in self.client_id_to_position.items():
            enemy_position = self.client_id_to_enemy_position[client_id]

            x_dif = client_position[0] - enemy_position[0]
            y_dif = client_position[1] - enemy_position[1]

            if abs(x_dif) > abs(y_dif):
                if x_dif < 0:
                    enemy_position[0] -= 1
                elif x_dif > 0:
                    enemy_position[0] += 1
            else:
                if y_dif < 0:
                    enemy_position[1] -= 1
                elif y_dif > 0:
                    enemy_position[1] += 1


def run_server(my_ip: IPv4Address | None = None, port: int = 8888):
    if my_ip is None:
        my_ip: IPv4Address = get_my_ip()

    print(f"Server address - {my_ip}:{port}")

    server = Server(my_ip, port)
    server.start_accepting_new_clients()

    clock = pygame.time.Clock()

    while True:
        # Update the enemies for each client
        server.update_enemy_positions()

        # Send each client the position information
        server.send_position_information_to_each_client()

        # 60 times a second
        clock.tick(60)


if __name__ == "__main__":
    run_server()
