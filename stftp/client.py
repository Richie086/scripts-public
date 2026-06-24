import socket
import ssl
import struct

# --- Protocol Framing Logic ---
def send_message(sock, opcode, payload: bytes):
    # Length is the size of the payload + 1 byte for the opcode itself
    msg_length = len(payload) + 1
    
    # '!H B' means: Network byte order (!), Unsigned Short (H, 2 bytes), Unsigned Char (B, 1 byte)
    header = struct.pack('!HB', msg_length, opcode)
    
    # Send the header followed by the payload
    sock.sendall(header + payload)

# --- Connection Logic ---
# 1. Configure TLS Context
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# 2. Create raw TCP Socket
raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 3. Wrap the socket BEFORE connecting (ensure port matches your server)
secure_sock = context.wrap_socket(raw_socket, server_hostname='127.0.0.1')
secure_sock.connect(('127.0.0.1', 7070))

print("TLS connection established!")

# 4. Send a test message
# Opcode 0x01 (Read), Payload "test.txt"
send_message(secure_sock, 0x01, b"test.txt")
print("Test message sent successfully.")

secure_sock.close()
