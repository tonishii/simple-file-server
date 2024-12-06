import sys
import socket
import threading
import os
from datetime import datetime
from typing import Optional

BUFFER = 128
FORMAT = "utf-8"
DIRECTORY = 'SERVERFILES'
registers = []

if not os.path.exists(DIRECTORY):
    print("[DIRECTORY] Creating a new server directory.")
    os.makedirs(DIRECTORY)

SERVER_HOST, SERVER_PORT = (sys.argv[1], int(sys.argv[2])) if len(sys.argv) > 1 else (socket.gethostbyname(socket.gethostname()), 5050)

def encode_to_bytes(data: str) -> bytes:
    """Encodes the length of data into a fixed-size byte array."""
    return str(len(data)).encode(FORMAT).ljust(BUFFER)

def recv_data(client_socket) -> bytes:
    """Receives header containing length of data then receives data of said length

    :param socket client_socket: Current connection of the client
    :return bytes: Returns the data decoded of specified FORMAT
    """
    data_length = int(client_socket.recv(BUFFER).decode(FORMAT))
    return client_socket.recv(data_length)

def store_file(client_socket, filename, reg) -> None:
    """Stores the file in the directory of the server.

    :param socket client_socket: Current connection of the client
    :param str filename: Name of the file to be stored in the server directory
    """
    filepath = os.path.join(DIRECTORY, filename)
    received, filesize = 0, int(client_socket.recv(BUFFER).decode(FORMAT))

    try:
        with open(filepath, "wb") as f:
            while received < filesize:
                bytes_read = client_socket.recv(BUFFER)
                received += len(bytes_read)
                f.write(bytes_read)

        print(f"[DIRECTORY] {reg} has uploaded {filename} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.")
        response = f"{reg}{datetime.now().strftime("<%Y-%m-%d %H:%M:%S>")}:\nUploaded\n{filename}"
        client_socket.sendall(encode_to_bytes(response))
        client_socket.sendall(response.encode(FORMAT))

    except:
        response = "Error: File receiving aborted."
        client_socket.sendall(encode_to_bytes(response))
        client_socket.sendall(response.encode(FORMAT))

def get_dir(client_socket) -> None:
    """Sends the list directory of the server through the connection of the client

    :param socket client_socket: Current connection of the client
    """
    file_list = os.listdir(DIRECTORY)
    msg = "\n".join(file_list) if file_list else "Server directory is empty"

    client_socket.sendall(encode_to_bytes(msg))
    client_socket.sendall(msg.encode(FORMAT))

def send_file(client_socket, filename) -> None:
    """Sends the file through the connection of the client

    :param socket client_socket: Current connection of the client
    :param str filename: Name of the file to be sent to the client connection
    """
    filepath = os.path.join(DIRECTORY, filename)

    if os.path.exists(filepath):
        client_socket.sendall(b'1')

        # Send the size of the file
        with open(filepath, "rb") as f:
            file_size = os.path.getsize(filepath)
            client_socket.sendall(f"{file_size}".ljust(BUFFER).encode(FORMAT))

            while bytes_read := f.read(BUFFER):
                # read the bytes from the file
                client_socket.sendall(bytes_read)
    else:
        client_socket.sendall(b'0')

def register_client(client_socket, reg) -> Optional[str]:
    if reg in registers:
        client_socket.sendall(b'0')
        return None

    registers.append(reg)
    print(f"[CONNECTION] Active registers: {", ".join(registers)}")
    print(f"[CONNECTION] Register added to the server: {reg}.")
    client_socket.sendall(b'1')

    return reg

def handle_client(client_socket, addr) -> None:
    reg = None
    while True:
        try:
            request = client_socket.recv(BUFFER).decode(FORMAT)
            data = recv_data(client_socket)

            print(request, data, reg)

            if request == "/register":
                reg = register_client(client_socket, data.decode(FORMAT))

            elif request == "/get":
                send_file(client_socket, data.decode(FORMAT))

            elif request == "/store":
                store_file(client_socket, data.decode(FORMAT), reg)

            elif request == "/dir":
                get_dir(client_socket)

            elif request == "/leave":
                break

        except ConnectionError:
            print(f"[ERROR] Client side connection abruptly closed.")
            break

    if reg:
        registers.remove(reg)

    print(f"[CONNECTION] Client has disconnected from server: {addr[0]} {addr[1]}.")
    client_socket.close()

if __name__ == "__main__":
    active = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        print(f"[STARTING] Binding server with address and port number: {SERVER_HOST} {SERVER_PORT}")
        print("[STARTING] Server is accepting connections.")

        server.bind((SERVER_HOST, SERVER_PORT))
        server.listen()

        while active:
            conn, addr = server.accept()
            print(f"[CONNECTION] Client connected to server: {addr[0]} {addr[1]}.")
            print(f"[CONNECTION] Active connections: {threading.active_count()}.")

            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()