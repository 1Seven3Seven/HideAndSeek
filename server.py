import socket
import threading
from ipaddress import IPv4Address

import pygame.time
import select

from get_my_ip import get_my_ip

ENCODING = "UTF-8"


class ClientPosition:
    def __init__(self, client_socket: socket.socket, client_address: tuple[str, int], initial_x: int, initial_y: int):
        self.x: int = initial_x
        self.y: int = initial_y

        self.client_socket: socket.socket | None = client_socket
        self.client_address: tuple[str, int] = client_address

        self._receive_position_stop_event: threading.Event = threading.Event()
        self._receive_position_thread: threading.Thread | None = None

    @property
    def position(self):
        return self.x, self.y

    def _receive_position(self) -> None:
        while not self._receive_position_stop_event.is_set():
            readable, _, _ = select.select([self.client_socket], [], [], 0.1)

            if readable:
                client_position_str = self.client_socket.recv(1024).decode(ENCODING)

                x, y = client_position_str.split(",")
                self.x = int(x)
                self.y = int(y)

    def start_receiving_position(self) -> None:
        if self._receive_position_thread is not None:
            return

        self._receive_position_thread = threading.Thread(
            target=self._receive_position,
            name=f"ClientPosition.receive_position_thread for client at address "
                 f"{self.client_address[0]}:{self.client_address[1]}"
        )
        self._receive_position_thread.start()

    def stop_receiving_position(self) -> None:
        self._receive_position_stop_event.set()
        self._receive_position_thread.join()


def server(my_ip: IPv4Address | None = None, port: int = 8888):
    if my_ip is None:
        my_ip: IPv4Address = get_my_ip()

    print(f"Server address - {my_ip}:{port}")

    my_socket = socket.socket()
    my_socket.bind((str(my_ip), port))

    my_socket.listen(1)

    print("Waiting for client")
    client_socket, client_addr = my_socket.accept()
    print(f"Client address - {client_addr[0]}:{client_addr[1]}")

    input("Press enter to start.")

    client_socket.sendall("Start".encode(ENCODING))

    print("Receiving initial position")
    msg = client_socket.recv(1024)
    msg = msg.decode(ENCODING)
    if not msg.startswith("Initial Position:"):
        print(f"Initial position message '{msg}' is in an incorrect format")
        client_socket.close()
        my_socket.close()
        exit(1)

    _, msg = msg.split(":")
    print(f"Received initial position: {msg}")

    x, y = msg.split(",")

    enemy_position = [int(x), int(y)]
    client_position = ClientPosition(client_socket, client_addr, int(x), int(y))
    client_position.start_receiving_position()

    clock = pygame.time.Clock()

    while True:
        x_dif = client_position.x - enemy_position[0]
        y_dif = client_position.y - enemy_position[1]

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

        client_socket.sendall(
            f"{enemy_position[0]},{enemy_position[1]}:{client_position.x},{client_position.y}".encode(ENCODING)
        )

        clock.tick(60)


if __name__ == "__main__":
    server(my_ip=get_my_ip())
