import os
import signal
import time
import socket
import sys

WATCHDOG_TIMEOUT = 10  # Timeout value in seconds
server_ip = ""  # Global variable to hold the server IP

def handle_watchdog_signal(signum, frame):
    global server_ip
    print(f"Server {server_ip} cannot be reached.")
    sys.exit(0)

def main():
    global server_ip

    signal.signal(signal.SIGUSR1, handle_watchdog_signal)

    # Get the IP address of the server (localhost)
    server_ip = socket.gethostbyname("localhost")

    while True:
        start_time = time.time()
        time.sleep(WATCHDOG_TIMEOUT)
        elapsed_time = time.time() - start_time

        # Check if the elapsed time exceeds the timeout
        if elapsed_time >= WATCHDOG_TIMEOUT:
            handle_watchdog_signal(signal.SIGUSR1, None)

if __name__ == "__main__":
    main()
