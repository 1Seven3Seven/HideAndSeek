import socket
from ipaddress import IPv4Address


def get_my_ip() -> IPv4Address:
    return IPv4Address(socket.gethostbyname(socket.gethostname()))
