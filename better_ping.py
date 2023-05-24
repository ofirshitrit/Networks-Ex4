import os
import struct
import socket
import select
import sys
import time
from subprocess import Popen
import signal

ICMP_ECHO_REQUEST = 8  # ICMP Echo Request type code

def calculate_checksum(data):
    # Helper function to calculate the checksum
    checksum = 0
    for i in range(0, len(data), 2):
        checksum += (data[i] << 8) + data[i + 1]
    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += checksum >> 16
    return ~checksum & 0xffff

def send_ping_request(dest_addr, seq_number):
    # Create a raw socket
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    icmp_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, 64)

    # Build the ICMP packet
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, seq_number, 1)
    data = struct.pack('!d', time.time())
    checksum = calculate_checksum(header + data)
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, checksum, seq_number, 1)

    # Send the ICMP packet
    icmp_socket.sendto(header + data, (dest_addr, 1))
    return time.time()  # Return the send time

def receive_ping_reply(icmp_socket, seq_number, timeout):
    start_time = time.time()

    while True:
        # Check if timeout has occurred
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            return None
        ready, _, _ = select.select([icmp_socket], [], [], timeout - elapsed_time)
        if ready:
            # Receive the ICMP reply packet
            packet, addr = icmp_socket.recvfrom(1024)
            icmp_header = packet[20:28]
            type_code, _, _, received_seq, _ = struct.unpack('!BBHHH', icmp_header)
            if type_code == 0 and received_seq == seq_number:
                return addr[0], time.time()

def ping_host(host, watchdog_pid):
    try:
        dest_addr = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Cannot resolve {host}: Unknown host")
        return

    print(f"Pinging {host} [{dest_addr}] with 32 bytes of data:")

    seq_number = 1
    timeout = 1  # seconds

    # Create a raw socket
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    while True:
        send_time = send_ping_request(dest_addr, seq_number)
        reply = receive_ping_reply(icmp_socket, seq_number, timeout)

        if reply:
            ip, reply_time = reply
            rtt = (reply_time - send_time) * 1000  # Calculate Round-Trip Time in milliseconds
            print(f"Reply from {ip}: icmp_seq={seq_number}, time={rtt:.2f} ms")
        else:
            print(f"No reply from {host}: icmp_seq={seq_number}")

        seq_number += 1

        # Update the watchdog timer
        os.kill(watchdog_pid, signal.SIGUSR1)

        time.sleep(1)


def establish_tcp_connection():
    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the watchdog process
    server_address = ("localhost", 3000)
    tcp_socket.connect(server_address)

    return tcp_socket

def keep_alive(tcp_socket):
    # Send periodic messages to keep the TCP connection alive
    while True:
        tcp_socket.sendall(b"PING")
        time.sleep(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python better_ping.py <ip>")
        return

    host = sys.argv[1]

    # Spawn the watchdog process
    watchdog_pid = os.fork()
    if watchdog_pid == 0:
        # Child process - Run the watchdog.py script
        python_executable = sys.executable  # Path to the python executable
        Popen([python_executable, "watchdog.py"])
        sys.exit(0)

    # Establish TCP connection with the watchdog process
    tcp_socket = establish_tcp_connection()

    # Parent process - Run the ping_host function
    ping_host(host, watchdog_pid)

    # Close the TCP connection before exiting
    tcp_socket.close()

if __name__ == "__main__":
    main()