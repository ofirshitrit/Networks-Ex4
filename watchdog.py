import socket
import time


def start_watchdog():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', 3000))
    sock.listen(1)
    print("Watchdog timer is running.")

    while True:
        connection, address = sock.accept()
        connection.close()


if __name__ == "__main__":
    start_watchdog()
