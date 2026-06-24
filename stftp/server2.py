import socket
import ssl
import os
import struct
import threading

# --- Server Configuration ---
PORT = 7070
HOST = '192.168.0.51'
UPLOAD_DIR = "stftpupload"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# TFTP Opcodes
OP_RRQ = 0x01
OP_WRQ = 0x02
OP_ACK = 0x04
OP_ERROR = 0x05

def handle_client(raw_conn, addr, context):
    """Handles an individual client connection, wrapped in TLS."""
    print(f"[+] New raw connection established from {addr}")
    
    try:
        # 1. UPGRADE TO TLS: Wrap the socket before reading any data
        secure_conn = context.wrap_socket(raw_conn, server_side=True)
        print(f"[*] TLS Handshake successful with {addr}")

        # 2. Read the 2-byte Length header
        raw_length = secure_conn.recv(2)
        if not raw_length:
            return
        msg_length = struct.unpack('!H', raw_length)[0]
        
        # 3. Read the Opcode and the Filename Payload
        remaining_data = secure_conn.recv(msg_length)
        opcode = remaining_data[0]
        raw_filename = remaining_data[1:].decode('utf-8')
        
        # 4. Security Check
        safe_filename = os.path.basename(raw_filename)
        filepath = os.path.join(UPLOAD_DIR, safe_filename)
        
        # 5. Handle Read Request (Download)
        if opcode == OP_RRQ:
            print(f"[{addr}] Requested Download: {safe_filename}")
            if not os.path.exists(filepath):
                print(f"[{addr}] ERROR: File not found.")
                secure_conn.sendall(bytes([OP_ERROR]) + b"File not found")
                return
            
            with open(filepath, 'rb') as f:
                secure_conn.sendall(f.read())
            print(f"[{addr}] Download complete.")

        # 6. Handle Write Request (Upload)
        elif opcode == OP_WRQ:
            print(f"[{addr}] Requested Upload: {safe_filename}")
            
            # Send an ACK (0x04)
            secure_conn.sendall(bytes([0x04]))
            
            with open(filepath, 'wb') as f:
                while True:
                    data = secure_conn.recv(4096)
                    if not data:
                        break 
                    f.write(data)
            print(f"[{addr}] Upload complete and securely saved.")

        else:
            print(f"[{addr}] ERROR: Unknown Opcode {hex(opcode)}")
            secure_conn.sendall(bytes([OP_ERROR]) + b"Invalid Opcode")

    except ssl.SSLError as e:
        print(f"[-] TLS Handshake failed with {addr}: {e}")
    except Exception as e:
        print(f"[-] Connection error with {addr}: {e}")
    finally:
        # Closing the secure wrapper also closes the underlying raw socket
        try:
            secure_conn.close()
        except NameError:
            raw_conn.close()
        print(f"[-] Connection closed with {addr}")

def main():
    # --- Setup TLS Context ---
    # Ensure cert.pem and key.pem are in the same directory as this script!
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # Setup the TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Secure TCP File Server listening on {HOST}:{PORT}...")
    print(f"[*] Storage mapped to: ./{UPLOAD_DIR}/")

    try:
        while True:
            # Accept the raw TCP connection
            raw_conn, addr = server.accept()
            
            # Pass the raw connection AND the TLS context into the thread
            client_thread = threading.Thread(
                target=handle_client, 
                args=(raw_conn, addr, context)
            )
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\n[*] Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
