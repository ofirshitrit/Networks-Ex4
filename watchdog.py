import os
import signal
import time
import socket
import sys
from multiprocessing import Process

WATCHDOG_TIMEOUT = 10  # Timeout value in seconds
WATCHDOG_PORT = 4000  # Port number for the TCP connection

def handle_watchdog_signal(signum, frame):
    global server_ip
    print(f"Server {server_ip} cannot be reached.")
    sys.exit(0)

def keep_alive(tcp_socket):
    # Receive periodic "PING" messages to keep the TCP connection alive
    while True:
        message = tcp_socket.recv(1024)
        if not message:
            break

def main():
    global server_ip

    signal.signal(signal.SIGUSR1, handle_watchdog_signal)

    # Get the IP address of the server (localhost)
    server_ip = socket.gethostbyname("localhost")

    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set the SO_REUSEADDR and SO_REUSEPORT options
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Bind the socket to the port
    server_address = ("localhost", WATCHDOG_PORT)
    tcp_socket.bind(server_address)

    # Listen for incoming connections
    tcp_socket.listen(1)

    # Accept a connection
    connection, client_address = tcp_socket.accept()

    # Run the keep_alive function in a separate process
    keep_alive_process = Process(target=keep_alive, args=(connection,))
    keep_alive_process.start()

    while True:
        start_time = time.time()
        time.sleep(WATCHDOG_TIMEOUT)
        elapsed_time = time.time() - start_time

        # Check if the elapsed time exceeds the timeout
        if elapsed_time >= WATCHDOG_TIMEOUT:
            handle_watchdog_signal(signal.SIGUSR1, None)

    # Terminate the keep_alive process before exiting
    keep_alive_process.terminate()

if __name__ == "__main__":
    main()
