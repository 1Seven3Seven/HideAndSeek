import socket
from ipaddress import IPv4Address

from get_my_ip import get_my_ip

ENCODING = "UTF-8"


def server(my_ip: IPv4Address | None = None, port: int = 8888):
    if my_ip is None:
        my_ip: IPv4Address = get_my_ip()

    print(f"Server address - {my_ip}:{port}")

    my_socket = socket.socket()
    my_socket.bind((str(my_ip), port))

    my_socket.listen(1)

    print("Waiting for client")
    client_socket, _client_addr = my_socket.accept()
    print(f"Client address - {_client_addr[0]}:{_client_addr[1]}")

    input("Press enter to start.")

    client_socket.sendall("Start".encode(ENCODING))

    print("Receiving initial position")
    msg = client_socket.recv(2048)
    msg = msg.decode(ENCODING)
    if not msg.startswith("Initial Position:"):
        print(f"Initial position message '{msg}' is in an incorrect format")
        client_socket.close()
        my_socket.close()
        exit(1)

    _, msg = msg.split(":")
    print(f"Received initial position: {msg}")

    x, y = msg.split(",")
    player_position = [int(x), int(y)]

    enemy_position = player_position[:]

    while True:
        msg = client_socket.recv(2048)
        msg = msg.decode(ENCODING)

        x, y = msg.split(",")
        player_position = [int(x), int(y)]

        x_dif = player_position[0] - enemy_position[0]
        y_dif = player_position[1] - enemy_position[1]

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
            f"{enemy_position[0]},{enemy_position[1]}:{player_position[0]},{player_position[1]}".encode(ENCODING)
        )


if __name__ == "__main__":
    server(my_ip=get_my_ip())
