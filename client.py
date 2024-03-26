import socket
import threading
from ipaddress import IPv4Address

import pygame
import select

from get_my_ip import get_my_ip

ENCODING = "UTF-8"


class Client:
    def __init__(self, initial_x: int, initial_y: int, my_id: int, my_socket: socket.socket):
        self.x: int = initial_x
        self.y: int = initial_y

        self.id: int = my_id

        self.socket: socket.socket = my_socket

        self._update_position_information_stop_event: threading.Event | None = threading.Event()
        self._update_position_information_thread: threading.Thread | None = None

        self.client_id_to_client_position: dict[int, tuple[int, int]] = {}
        self.client_id_to_enemy_position: dict[int, tuple[int, int]] = {}

    @property
    def player_position(self) -> tuple[int, int]:
        return self.x, self.y

    @property
    def target_position(self) -> tuple[int, int]:
        return self.client_id_to_client_position[self.id]

    @property
    def enemy_position(self) -> tuple[int, int]:
        return self.client_id_to_enemy_position[self.id]

    def __update_position_information(self) -> None:
        while not self._update_position_information_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if not readable:
                continue

            position_information_string = self.socket.recv(2048).decode(ENCODING)


def run_client(server_ip: IPv4Address, port: int = 8888):
    print(f"Connecting to server at address - {server_ip}:{port}")
    my_socket = socket.socket()
    my_socket.connect((str(server_ip), port))
    print(" - done")

    print("Setting up pygame")
    pygame.init()
    pygame.display.set_caption("Title")
    window_size = (1280, 720)
    screen = pygame.display.set_mode(window_size)
    clock = pygame.time.Clock()

    print("Sending the initial position")
    initial_position = window_size[0] // 2, window_size[1] // 2
    initial_position_bytes = f"initial_position:{initial_position[0]},{initial_position[1]}".encode(ENCODING)
    my_socket.sendall(initial_position_bytes)

    print("Getting the id from the server")
    id_str = my_socket.recv(1024).decode(ENCODING)
    id_str = id_str[:-1]  # Remove the pipe
    my_id = int(id_str)

    print("Sending the id back to the server")
    id_bytes = f"{my_id}|".encode(ENCODING)
    my_socket.sendall(id_bytes)

    print("Creating client object")
    client = Client(initial_position[0], initial_position[1], my_id, my_socket)

    print("Waiting for start message")
    start_str = my_socket.recv(1024).decode(ENCODING)
    if not start_str == "start|":
        exit(1)

    print("Begin")
    to_break: bool = False

    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                to_break = True
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    to_break = True
                    break

        if to_break:
            break

        screen.fill((0, 0, 0))

        """BELOW"""

        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_w]:
            client.y -= 2
        if pressed[pygame.K_s]:
            client.y += 2
        if pressed[pygame.K_a]:
            client.x -= 2
        if pressed[pygame.K_d]:
            client.x += 2

        for other_client_id, other_client_position in client.client_id_to_client_position.items():
            if other_client_id == client.id:
                continue

            other_enemy_position = client.client_id_to_enemy_position[other_client_id]

            pygame.draw.circle(screen, (100, 100, 255), other_client_position, 10)
            pygame.draw.circle(screen, (255, 100, 100), other_enemy_position, 5)
            pygame.draw.line(screen, (255, 255, 255), other_client_position, other_enemy_position)

        pygame.draw.circle(screen, (255, 255, 255), client.player_position, 20)
        pygame.draw.circle(screen, (0, 255, 0), client.enemy_position, 10)
        pygame.draw.circle(screen, (255, 0, 0), client.target_position, 5)
        pygame.draw.line(screen, (255, 255, 255), client.enemy_position, client.target_position, 2)

        """ABOVE"""

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    run_client(get_my_ip())
