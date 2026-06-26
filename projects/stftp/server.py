import os

# Define the master folder where all incoming files will be trapped
UPLOAD_DIR = "./uploads/"

# Create the folder automatically if it doesn't exist yet
os.makedirs(UPLOAD_DIR, exist_ok=True)

import socket
import ssl
import struct

# --- Protocol Framing Logic ---
def receive_message(sock):
    # Read exactly 2 bytes to get the length of the incoming message
    raw_length = sock.recv(2)
    if not raw_length:
        return None, None # Connection closed
    
    # Unpack the 2 bytes into an integer
    msg_length = struct.unpack('!H', raw_length)[0]
    
    # Read the rest of the message based on that exact length
    # (Remember, msg_length includes the 1-byte opcode)
    remaining_data = sock.recv(msg_length)
    
    # Extract the opcode (the first byte) and the payload (everything else)
    opcode = remaining_data[0]
    payload = remaining_data[1:]
    
    return opcode, payload

# --- Connection Logic ---
# 1. Configure the TLS Context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
# Make sure cert.pem and key.pem are in the same directory as this script!
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

# 2. Setup the raw TCP Socket
bindsocket = socket.socket()

# --- ADD THIS LINE ---
# This tells the OS to reuse the local address immediately
bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Now bind to the port
bindsocket.bind(('127.0.0.1', 7070))
bindsocket.listen(5)
print("Listening on port 7070...")

print("Listening on port 7070...")

while True:
    raw_socket, fromaddr = bindsocket.accept()
    print(f"Connection from {fromaddr}")
    
    # 3. Wrap the socket in TLS
    try:
        secure_sock = context.wrap_socket(raw_socket, server_side=True)
        
        # 4. Use the secure socket to receive our framed data
        opcode, payload = receive_message(secure_sock)
        
        if opcode is not None:
            # Format the opcode as a hex string (e.g., '0x1') for easier reading
            print(f"Received Opcode: {hex(opcode)}")
            print(f"Received Payload: {payload.decode('utf-8')}")
        else:
            print("Client connected but sent no data.")
            
    except ssl.SSLError as e:
        print(f"TLS Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    finally:
        # Always gracefully close the socket when done
        secure_sock.close()
