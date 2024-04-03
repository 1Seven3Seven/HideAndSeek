import socket

from Logger import Logger
from ServerState import ServerState
from Utils import get_my_ip


def main() -> None:
    Logger.log(f"Connecting to server")
    client_socket = socket.socket()
    client_socket.settimeout(2)
    try:
        client_socket.connect((str(get_my_ip()), 8888))
    except TimeoutError:
        Logger.log("Connection request timed out")
        Logger.log("Closing socket")
        client_socket.close()
        return

    server_state = ServerState(client_socket)
    server_state.start_updater()

    Logger.log("Waiting for state updater thread to finish")
    server_state.state_updater_thread.join()
    server_state.stop_updater()


if __name__ == "__main__":
    main()
