import socket
import threading
from ipaddress import IPv4Address

import pygame
import select

from get_my_ip import get_my_ip

ENCODING = "UTF-8"


class EnemyInformation:
    def __init__(self, my_socket: socket.socket, initial_x: int, initial_y: int):
        self.enemy_x: int = initial_x
        self.enemy_y: int = initial_y

        self.target_x: int = initial_x
        self.target_y: int = initial_y

        self.socket: socket.socket = my_socket

        self._receive_enemy_info_stop_event: threading.Event = threading.Event()
        self._receive_enemy_info_thread: threading.Thread | None = None

    @property
    def enemy_position(self) -> tuple[int, int]:
        return self.enemy_x, self.enemy_y

    @property
    def target_position(self) -> tuple[int, int]:
        return self.target_x, self.target_y

    def _receive_enemy_info(self) -> None:
        while not self._receive_enemy_info_stop_event.is_set():
            readable, _, _ = select.select([self.socket], [], [], 0.1)

            if readable:
                enemy_target_str = self.socket.recv(1024).decode(ENCODING)
                enemy_str, target_str, *_ = enemy_target_str.split(":")

                enemy_x, enemy_y, *_ = enemy_str.split(",")
                self.enemy_x = int(enemy_x)
                self.enemy_y = int(enemy_y)

                target_x, target_y, *_ = target_str.split(",")
                self.target_x = int(target_x)
                self.target_y = int(target_y)

    def start_receiving_enemy_info(self) -> None:
        if self._receive_enemy_info_thread is not None:
            return

        self._receive_enemy_info_thread = threading.Thread(
            target=self._receive_enemy_info,
            name=f"EnemyPosition.receive_enemy_info_thread"
        )
        self._receive_enemy_info_thread.start()

    def stop_receiving_enemy_info(self) -> None:
        self._receive_enemy_info_stop_event.set()
        self._receive_enemy_info_thread.join()


def client(server_ip: IPv4Address, port: int = 8888):
    print(f"Connecting to server at address - {server_ip}:{port}")
    my_socket = socket.socket()
    my_socket.connect((str(server_ip), port))
    print(" - done")

    print("Waiting for server to start")
    msg = my_socket.recv(1024)
    msg = msg.decode(ENCODING)

    if msg != "Start":
        print(f"Incorrect start message '{msg}'")
        exit(1)

    print("Server started")

    pygame.init()
    pygame.display.set_caption("Title")
    window_size = (1280, 720)
    screen = pygame.display.set_mode(window_size)
    clock = pygame.time.Clock()

    player_position = [window_size[0] // 2, window_size[1] // 2]
    enemy_information = EnemyInformation(my_socket, player_position[0], player_position[1])
    enemy_information.start_receiving_enemy_info()

    print("Sending initial position")
    my_socket.sendall(f"Initial Position:{player_position[0]},{player_position[1]}".encode(ENCODING))

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
            player_position[1] -= 2
        if pressed[pygame.K_s]:
            player_position[1] += 2
        if pressed[pygame.K_a]:
            player_position[0] -= 2
        if pressed[pygame.K_d]:
            player_position[0] += 2

        pygame.draw.circle(screen, (255, 255, 255), player_position, 20)
        pygame.draw.circle(screen, (0, 255, 0), enemy_information.enemy_position, 10)
        pygame.draw.circle(screen, (255, 0, 0), enemy_information.target_position, 5)
        pygame.draw.line(screen, (255, 255, 255),
                         enemy_information.enemy_position, enemy_information.target_position,
                         2)

        my_socket.sendall(f"{player_position[0]},{player_position[1]}".encode(ENCODING))

        """ABOVE"""

        pygame.display.flip()
        clock.tick(60)

    enemy_information.stop_receiving_enemy_info()
    my_socket.close()


if __name__ == "__main__":
    client(get_my_ip())
