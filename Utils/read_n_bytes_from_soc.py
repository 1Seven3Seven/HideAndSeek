import socket


def read_n_bytes_from_soc(soc: socket.socket, n: int) -> bytes:
    """
    Reads `n` bytes from the given socket.

    :param soc: The socket to read from.
    :param n: The number of bytes to read.
    :return: The bytes read from the socket.
    :raises OSError: If `soc.recv()` returns an empty bytes object `b''`.
    """

    received_bytes: bytearray = bytearray()
    while (num_received_bytes := len(received_bytes)) < n:
        chunk: bytes = soc.recv(n - num_received_bytes)
        if chunk:
            received_bytes.extend(chunk)
        else:
            raise OSError("Unable to read data from socket")

    return received_bytes
