import socket
import ipaddress
import os

BUFFER = 128
FORMAT = "utf-8"

# List of available commands in the application
commands = {
    "/join <server_ip_add> <port>": "Connect to the server application",
    "/leave": "Disconnect from the server application",
    "/register <handle>": "Register a unique handle or alias",
    "/store <filename>": "Send file to server",
    "/dir ": "Request directory file list from the server",
    "/get <filename>": "Fetch a file from the server",
    "/exit": "Exit from the application"
}

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

def is_valid_addr(ip_addr: str) -> bool:
    """Checks the given IP address is valid.

    :param str ip_addr: ip address to be validated
    :return bool: Returns if the address passed is in v4/v6 format
    """
    try:
        ipaddress.ip_address(ip_addr)
        return True
    except ValueError:
        return False

def is_valid_port(port: int) -> bool:
    """Checks if the port number is valid.

    :param int port: port number to be validated
    :return bool: returns if the port number is properly formatted and of the correct type
    """
    try:
        return 1 <= port <= 65535
    except (ValueError, TypeError):
        return False

def print_commands() -> None:
    """Print the available commands in the application."""

    print("\nCommands:")
    for cmd, desc in commands.items():
        print(f"   {cmd.ljust(30)} {desc}")
    print()

def send_file(filename: str, client_socket: socket.socket) -> None:
    """Sends a file to the specified socket.

    :param str reg: register of the client
    :param socket.socket client_socket: current socket used by the client
    """

    # Check if the file exists in the current directory
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return

    # Send the size of the file
    with open(filename, "rb") as f:
        filesize = os.path.getsize(filename)
        client_socket.sendall(f"{filesize}".ljust(BUFFER).encode(FORMAT))

        while bytes_read := f.read(BUFFER):
            # read the bytes from the file
            client_socket.sendall(bytes_read)

    print(recv_data(client_socket).decode(FORMAT))

def receive_file(filename: str, client_socket: socket.socket) -> None:
    """Receives a file from the specified socket and write it to a file.

    :param str filename: filename to be received from the server
    :param socket.socket client_socket: current socket used by the client
    """

    if client_socket.recv(1) == b'0':
        print("Error: File was not found.")
        return

    received, filesize = 0, int(client_socket.recv(BUFFER).decode(FORMAT))

    with open(filename, "wb") as f:
        while received < filesize:
            bytes_read = client_socket.recv(BUFFER)
            received += len(bytes_read)
            f.write(bytes_read)

    print(f"File received from Server: {filename}")

def execute_command(client_socket: socket.socket, reg: str, command: str) -> str:
    """Executes the command given by the user.

    :param socket.socket client_socket: current socket used by the client
    :param str reg: register of the client
    :param str command: command given by the user
    :return str: returns the register/handle/alias of the client at the execution of the command
    """

    if command.startswith('/register'):
        if reg is not None:
            print("Error: Registration failed. Already registered to the server")
            return reg

        parts = command.split(" ", 1)

        if len(parts) < 2:
            print("Error: Command parameters do not match or is not allowed")
            return reg

        command, handle = parts

        client_socket.sendall(command.encode(FORMAT))

        client_socket.sendall(encode_to_bytes(handle))
        client_socket.sendall(handle.encode(FORMAT))

        status = client_socket.recv(1)

        if status == b'1':
            print(f"Welcome {handle}!")
            return handle

        elif status == b'0':
            print("Error: Registration failed. Handle or alias already exists.")
            return None

    elif command.startswith('/store'):
        if reg is not None:
            parts = command.split(" ", 1)

            if len(parts) < 2:
                print("Error: Command parameters do not match or is not allowed")
                return reg

            command, filename = parts
            print(command, filename)

            client_socket.sendall(command.encode(FORMAT))
            client_socket.sendall(encode_to_bytes(filename))
            client_socket.sendall(filename.encode(FORMAT))

            send_file(filename, client_socket)
        else:
            print("Error: No register entered in the server.")

    elif command.startswith('/get'):
        if reg is not None:
            parts = command.split(" ", 1)

            if len(parts) < 2:
                print("Error: Command parameters do not match or is not allowed")
                return reg

            command, filename = parts

            client_socket.sendall(command.encode(FORMAT))
            client_socket.sendall(encode_to_bytes(filename))
            client_socket.sendall(filename.encode(FORMAT))

            receive_file(filename, client_socket)
        else:
            print("Error: No register entered in the server")

    elif command == '/dir':
        if reg is not None:
            client_socket.sendall(command.encode(FORMAT))

            client_socket.sendall(b'1')
            client_socket.sendall(b' ')

            print(recv_data(client_socket).decode(FORMAT))
        else:
            print("Error: No register entered in the server.")

    elif command == '/leave':
        client_socket.sendall(command.encode(FORMAT))
        client_socket.sendall(b'1')
        client_socket.sendall(b' ')
        return None

    else:
        print("Error: Command not found")

    return reg

def handle_commands() -> None:
    """Handles the input given by the user
    :raises ValueError: raises this error when invalid parameters were met when inputting the command
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        reg, active = None, False

        while True:
            command = input("Enter command: ").strip()

            if command.startswith('/join'):
                # Check if HOST and PORT is valid
                try:
                    _, HOST, PORT = command.split(" ", 2)
                    PORT = int(PORT)

                    if not is_valid_addr(HOST) or not is_valid_port(PORT):
                        raise ValueError

                    client_socket.connect((HOST, PORT))
                    active = True
                    print("Connected to the File Exchange Server successfully!")

                except (ValueError, OSError):
                    print("Error: Connection to the Server has failed! Please check IP Address and Port Number.")

            elif command == '/?':
                print_commands()

            elif not active and command == '/leave':
                print("Error: Disconnection failed. Please connect to the server first.")

            elif active:
                reg = execute_command(client_socket, reg, command)

                if reg is None and command == '/leave':
                    print("Connection closed. Thank you!")
                    active = False

            elif command == '/exit':
                print("Exiting application!")
                break

            elif any(command.startswith(key) for key in commands.keys()):
                print("Error: Command not found.")

            else:
                print("Error: Please connect to the server first")

if __name__ == "__main__":
    try:
        handle_commands()
    except ConnectionError:
        print("Error: Server side connection abruptly closed")
    except KeyboardInterrupt:
        print("Connection closed. Thank you!")