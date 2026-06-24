import socket
import ssl
import struct
import sys
import os

# --- Client Configuration ---
HOST = '192.168.0.51'
PORT = 7070

# TFTP Opcodes
OP_RRQ = 0x01
OP_WRQ = 0x02
OP_ACK = 0x04
OP_ERROR = 0x05

def get_secure_context():
    """Creates an SSL context that trusts our self-signed cert for local testing."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def send_request(sock, opcode, filename):
    """Helper function to frame and send the initial request header."""
    payload = filename.encode('utf-8')
    msg_length = len(payload) + 1 
    
    header = struct.pack('!HB', msg_length, opcode)
    sock.sendall(header + payload)

def upload_file(filepath):
    """Handles the OP_WRQ (Upload) state machine securely."""
    if not os.path.exists(filepath):
        print(f"[-] Error: Local file '{filepath}' does not exist.")
        return

    filename = os.path.basename(filepath)
    context = get_secure_context()

    # 1. Create the raw socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
        # 2. UPGRADE TO TLS: Wrap the socket BEFORE connecting
        with context.wrap_socket(raw_sock, server_hostname=HOST) as secure_sock:
            try:
                # Connect using the secure socket
                secure_sock.connect((HOST, PORT))
                print(f"[*] TLS Connection established to {HOST}:{PORT}")

                send_request(secure_sock, OP_WRQ, filename)

                response = secure_sock.recv(1)
                if not response:
                    print("[-] Server dropped the connection unexpectedly.")
                    return
                    
                if response[0] == OP_ERROR:
                    err_msg = secure_sock.recv(1024).decode('utf-8', errors='ignore')
                    print(f"[-] Server rejected upload: {err_msg}")
                    return
                elif response[0] != OP_ACK:
                    print(f"[-] Protocol mismatch. Expected ACK (0x04), got {hex(response[0])}")
                    return

                print("[*] Server is ready. Streaming encrypted file data...")

                with open(filepath, 'rb') as f:
                    secure_sock.sendall(f.read())
                    
                print("[+] Upload successful!")

            except ssl.SSLError as e:
                print(f"[-] TLS Handshake failed: {e}")
            except ConnectionRefusedError:
                print(f"[-] Connection refused. Is the server running on port {PORT}?")
            except Exception as e:
                print(f"[-] Upload failed: {e}")

def download_file(filename, save_path=None):
    """Handles the OP_RRQ (Download) state machine securely."""
    if save_path is None:
        save_path = f"downloaded_{filename}"

    context = get_secure_context()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=HOST) as secure_sock:
            try:
                secure_sock.connect((HOST, PORT))
                print(f"[*] TLS Connection established to {HOST}:{PORT}")

                send_request(secure_sock, OP_RRQ, filename)
                
                first_chunk = secure_sock.recv(4096)
                if not first_chunk:
                    print("[-] Server closed connection (file might be empty).")
                    return

                if first_chunk[0] == OP_ERROR:
                    err_msg = first_chunk[1:].decode('utf-8', errors='ignore')
                    print(f"[-] Server error: {err_msg}")
                    return

                print(f"[*] Downloading '{filename}' to '{save_path}' securely...")

                with open(save_path, 'wb') as f:
                    f.write(first_chunk) 
                    while True:
                        data = secure_sock.recv(4096)
                        if not data:
                            break 
                        f.write(data)
                        
                print("[+] Download successful!")

            except ssl.SSLError as e:
                print(f"[-] TLS Handshake failed: {e}")
            except ConnectionRefusedError:
                print(f"[-] Connection refused. Is the server running on port {PORT}?")
            except Exception as e:
                print(f"[-] Download failed: {e}")

def print_usage():
    print("Usage:")
    print("  python3 client.py upload <local_filepath>")
    print("  python3 client.py download <remote_filename>")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    target = sys.argv[2]

    if command == "upload":
        upload_file(target)
    elif command == "download":
        download_file(target)
    else:
        print(f"Unknown command: {command}")
        print_usage()
