import socket

from Utils import Logger


class ClientHandler(Logger):
    def __init__(self, client_id: int, client_socket: socket.socket, client_address: tuple[str, int]):
        self.client_id: int = client_id

        self.socket: socket.socket = client_socket
        self.address: tuple[str, int] = client_address
