import sys
import socket
import threading
import os
from datetime import datetime
from typing import Optional

BUFFER = 1024
FORMAT = "utf-8"
DIRECTORY = 'SERVERFILES'

# Stores the active registers in the server
registers = []

# Get the designated host and port
# Default is the host's name and port number 5050
SERVER_HOST, SERVER_PORT = (socket.gethostbyname(socket.gethostname()), int(sys.argv[1])) if len(sys.argv) == 2 else \
                           (sys.argv[1], int(sys.argv[2])) if len(sys.argv) == 3 else \
                           (socket.gethostbyname(socket.gethostname()), 5050)

# Create a new directory if none exists
if not os.path.exists(DIRECTORY):
    print("[DIRECTORY] Creating a new server directory.")
    os.makedirs(DIRECTORY)

def encode_to_bytes(data: str) -> bytes:
    """Encodes the length of data into a fixed-size byte array.

    :param str data: data to be encoded for sending its size
    :return bytes: returns the size of data in bytes
    """
    return str(len(data)).encode(FORMAT).ljust(BUFFER)

def recv_data(client_socket: socket.socket) -> bytes:
    """Receives header containing length of data then receives data of said length.

    :param socket.socket client_socket: current connection of the client
    :return bytes: returns the data decoded of specified FORMAT
    """
    data_length = int(client_socket.recv(BUFFER).decode(FORMAT))
    return client_socket.recv(data_length)

def send_file(client_socket: socket.socket, filename: str) -> None:
    """Sends the file through the connection of the client.

    :param socket.socket client_socket: current connection of the client
    :param str filename: name of the file to be sent to the client connection
    """

    # Get the filepath to the servers DIRECTORY
    filepath = os.path.join(DIRECTORY, filename)

    if os.path.exists(filepath):
        # Send the OK status flag to the client
        client_socket.sendall(b'1')

        # Send the file size to the client
        file_size = os.path.getsize(filepath)
        client_socket.sendall(f"{file_size}".ljust(BUFFER).encode(FORMAT))

        with open(filepath, "rb") as f:
            while bytes_read := f.read(BUFFER):
                # Read the bytes from the file until EOF
                client_socket.sendall(bytes_read)
    else:
        # Send the 0 status flag to the client
        client_socket.sendall(b'0')

def store_file(client_socket: socket.socket, filename: str, reg: str) -> None:
    """Stores the file in the directory of the server.

    :param socket.socket client_socket: current connection of the client
    :param str filename: name of the file to be stored in the server directory
    :param str reg: handle of the currently connected client
    """

    # Get the filepath to the servers DIRECTORY
    filepath = os.path.join(DIRECTORY, filename)

    # Get the file size to be received from the client
    received, filesize = 0, int(client_socket.recv(BUFFER).decode(FORMAT))

    try:
        with open(filepath, "wb") as f:
            while received < filesize:
                # Read the bytes from the file until all bytes are received
                bytes_read = client_socket.recv(BUFFER)

                received += len(bytes_read)

                # Write to the file
                f.write(bytes_read)

        # Print confirmation message and send respone to the client
        print(f"[DIRECTORY] {reg} has uploaded {filename} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.")
        response = f"{reg}{datetime.now().strftime("<%Y-%m-%d %H:%M:%S>")}:\nUploaded\n{filename}"
        client_socket.sendall(encode_to_bytes(response))
        client_socket.sendall(response.encode(FORMAT))

    except:
        # Send error response to the client
        response = "Error: File receiving aborted."
        client_socket.sendall(encode_to_bytes(response))
        client_socket.sendall(response.encode(FORMAT))

def get_dir(client_socket: socket.socket) -> None:
    """"Sends the server's list of files/directory through the connection of the client

    :param socket.socket client_socket: current connection of the client
    """

    # Get the servers directory
    file_list = os.listdir(DIRECTORY)

    # Join everything using a new line else if empty then the default string/msg
    msg = "Server Directory\n" + "\n".join(file_list) if file_list else "Server Directory is empty"

    client_socket.sendall(encode_to_bytes(msg))
    client_socket.sendall(msg.encode(FORMAT))

def register_client(client_socket: socket.socket, reg: str) -> Optional[str]:
    """Registers the clients handle received by the server

    :param socket.socket client_socket: current connection of the client
    :param str reg: handle/register received by the server
    :return Optional[str]: return the clients handle, None if invalid
    """

    if reg in registers:
        # Send 0 status flag if handle already exists
        client_socket.sendall(b'0')
        return None

    # Add the handle to the active registers
    registers.append(reg)
    print(f"[CONNECTION] Active registers: {", ".join(registers)}")
    print(f"[CONNECTION] Register added to the server: {reg}.")

    # Send 1 status flag if handle is valid
    client_socket.sendall(b'1')

    return reg

def handle_client(client_socket: socket.socket, addr: str) -> None:
    reg = None # Holds the active/current handle of the client

    while True:
        try:
            # Get the request and the ff. data used in various commands
            request = client_socket.recv(BUFFER).decode(FORMAT)

            if request not in ["/dir", "/leave"]:
                data = recv_data(client_socket)

            # print(request, data, reg) # FOR CHECKING

            # Send to the appropriate command handlers
            match request:
                case "/register": reg = register_client(client_socket, data.decode(FORMAT))
                case "/get": send_file(client_socket, data.decode(FORMAT))
                case "/store": store_file(client_socket, data.decode(FORMAT), reg)
                case "/dir": get_dir(client_socket)
                case "/leave":
                    break

        except ConnectionError: # Happens ie. when the client was suddenly shutdown
            print("[ERROR] Connection abruptly closed. Disconnecting client.")
            break

        except ValueError: # Happens ie. when the client exits without using the /leave command
            print("[ERROR] Unknown request/data received. Disconnecting client.")
            break

    # Only remove reg when client was registered in the server
    if reg:
        registers.remove(reg)

    print(f"[CONNECTION] Client has disconnected from server: {addr[0]} {addr[1]}.")
    client_socket.close()

if __name__ == "__main__":
    # Activate the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        print(f"[STARTING] Binding server with address and port number: {SERVER_HOST} {SERVER_PORT}")
        print("[STARTING] Server is accepting connections.")

        # Bind to the address
        server.bind((SERVER_HOST, SERVER_PORT))
        server.listen()

        while True:
            conn, addr = server.accept()
            print(f"[CONNECTION] Client connected to server: {addr[0]} {addr[1]}.")
            print(f"[CONNECTION] Active connections: {threading.active_count()}.")

            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()