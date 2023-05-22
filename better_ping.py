import os
import struct
import socket
import select
import sys
import time

ICMP_ECHO_REQUEST = 8  # ICMP Echo Request type code

def calculate_checksum(data):
    # Helper function to calculate the checksum
    checksum = 0
    for i in range(0, len(data), 2):
        checksum += (data[i] << 8) + data[i + 1]
    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += checksum >> 16
    return ~checksum & 0xffff


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
                # Retrieve the TTL value from the IP header
                ip_header = struct.unpack('!BBHHHBBH4s4s', packet[:20])
                ttl = ip_header[5]
                return addr[0], time.time(), ttl


def send_ping_request(dest_addr, seq_number, watchdog_socket, timeout):
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

    # Notify the watchdog that the reply is expected
    watchdog_socket.sendall(b"Reply arrived")

    start_time = time.time()  # Define start_time here

    while True:
        # Check if timeout has occurred
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            return None, None

        ready, _, _ = select.select([icmp_socket], [], [], timeout - elapsed_time)
        if ready:
            # Receive the ICMP reply packet
            packet, addr = icmp_socket.recvfrom(1024)
            icmp_header = packet[20:28]
            type_code, code, checksum, received_seq, received_ttl = struct.unpack('!BBHHH', icmp_header)

            if type_code == 0 and received_seq == seq_number:
                return addr[0], received_ttl, time.time()

    return None, None, None


def ping_host(host):
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

    # Connect to the watchdog
    watchdog_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    watchdog_socket.connect(("localhost", 3000))

    while True:
        send_time = time.time()  # Get the send time before sending the ping request
        send_ping_request(dest_addr, seq_number, watchdog_socket, timeout)
        ip, ttl, reply_time = receive_ping_reply(icmp_socket, seq_number, timeout)

        if ip and ttl and reply_time:
            rtt = (reply_time - send_time) * 1000  # Calculate Round-Trip Time in milliseconds
            print(f"Reply from {ip}: icmp_seq={seq_number}, ttl={ttl}, time={rtt:.2f} ms")
        else:
            print(f"No reply from {host}: icmp_seq={seq_number}")
            break  # No reply, stop the program

        seq_number += 1
        time.sleep(1)

    watchdog_socket.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python better_ping.py <ip>")
        return

    host = sys.argv[1]
    ping_host(host)


if __name__ == "__main__":
    main()
