import os
import time
import socket

def watchdog_timer():
    timeout = 10  # 10 seconds
    start_time = time.time()

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            print(f"Server {host} cannot be reached.")
            os._exit(0)  # Exit the program

        time.sleep(0.001)


if __name__ == "__main__":
    host = "google.com"

    # Create and start the watchdog timer thread
    watchdog_timer()
