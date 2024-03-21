import socket
from ipaddress import IPv4Address

import pygame

from get_my_ip import get_my_ip

ENCODING = "UTF-8"


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
    enemy_position = player_position[:]
    target_position = player_position[:]

    print("Sending initial position")
    my_socket.sendall(f"Initial Position:{player_position[0]},{player_position[1]}".encode(ENCODING))

    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit(0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit(0)

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
        pygame.draw.circle(screen, (0, 255, 0), enemy_position, 10)
        pygame.draw.circle(screen, (255, 0, 0), target_position, 5)
        pygame.draw.line(screen, (255, 255, 255), enemy_position, target_position, 2)

        my_socket.sendall(f"{player_position[0]},{player_position[1]}".encode(ENCODING))

        msg = my_socket.recv(2048)
        msg = msg.decode(ENCODING)

        enemy_position_str, target_position_str = msg.split(":")
        x, y = enemy_position_str.split(",")
        enemy_position = [int(x), int(y)]
        x, y = target_position_str.split(",")
        target_position = [int(x), int(y)]

        """ABOVE"""

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    client(get_my_ip())
