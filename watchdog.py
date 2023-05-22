import socket
import time

def start_watchdog():
    timeout = 10  # seconds

    # Create a socket with TCP protocol
    watchdog_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    watchdog_socket.bind(("localhost", 3000))
    watchdog_socket.listen(1)

    print("Watchdog started. Listening on port 3000...")

    while True:
        # Accept incoming connection
        client_socket, _ = watchdog_socket.accept()
        start_time = time.time()

        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
            except socket.error:
                break

            elapsed_time = time.time() - start_time

            if elapsed_time > timeout:
                print("Timeout occurred. Closing connection...")
                client_socket.close()
                break

            if data == "Reply arrived":
                print(f"Reply received in {elapsed_time:.2f} seconds")
                start_time = time.time()

        client_socket.close()

    watchdog_socket.close()

if __name__ == "__main__":
    start_watchdog()
