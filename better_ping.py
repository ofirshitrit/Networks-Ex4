import os
import struct
import socket
import select
import time
from threading import Thread

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


# Rest of the code remains the same


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
    icmp_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, 64)

    while True:
        send_time = time.time()  # Get the send time before sending the ping request
        send_ping_request(dest_addr, seq_number)
        reply = receive_ping_reply(icmp_socket, seq_number, timeout)

        if reply:
            ip, reply_time, ttl = reply
            rtt = (reply_time - send_time) * 1000  # Calculate Round-Trip Time in milliseconds
            print(f"Reply from {ip}: icmp_seq={seq_number} RTT={rtt:.4f} milliseconds TTL={ttl}")
            update_watchdog_timer(ip, 10)  # Update the watchdog timer
        else:
            print(f"No reply from {host}: icmp_seq={seq_number}")

        seq_number += 1
        time.sleep(1)


def update_watchdog_timer(ip, timeout):
    # Update the watchdog timer by establishing a TCP connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, 3001))
        sock.close()
    except socket.error:
        pass


if __name__ == "__main__":
    ping_host("google.com")
