import socket
import ipaddress
import os

# Ensure that tqdm loads properly else the program will not use it
try:
    from tqdm import tqdm
    tqdm_available = True
except ImportError:
    tqdm = None
    tqdm_available = False

BUFFER = 1024
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

def is_filename(filename: str) -> bool:
    """Checks if the filename is valid.

    :param str filename: filename to be validated
    :return bool: returns if the filename is valid based on the regex evaluation
    """
    return os.path.basename(filename) == filename and not os.path.isdir(filename)

def print_commands() -> None:
    """Print the available commands in the application."""

    print("Commands:")
    for cmd, desc in commands.items():
        print(f"   {cmd.ljust(30)} {desc}")
    print()

def send_file(client_socket: socket.socket, filename: str) -> None:
    """Sends a file to the specified socket.

    :param socket.socket client_socket: current socket used by the client
    :param str reg: register of the client
    """

    # Send the file size to the server
    filesize = os.path.getsize(filename)
    client_socket.sendall(f"{filesize}".ljust(BUFFER).encode(FORMAT))

    # Load the progress bar
    if tqdm_available:
        progress_bar = tqdm(total=filesize, unit="B", unit_scale=True, unit_divisor=1024, desc="Sending")

    with open(filename, "rb") as f:
        while bytes_read := f.read(BUFFER):
            # Read the bytes from the file until EOF
            client_socket.sendall(bytes_read)

            # Update the progress bar
            if tqdm_available:
                progress_bar.update(len(bytes_read))

    if tqdm_available:
        progress_bar.close()

    # Print the message received from the server
    print(recv_data(client_socket).decode(FORMAT))

def store_file(client_socket: socket.socket, filename: str) -> None:
    """Receives a file from the specified socket and writes it to a file in the user's directory.

    :param socket.socket client_socket: current socket used by the client
    :param str filename: filename to be received from the server
    """

    # Server sends a 0 status flag if the file is not in the server
    if client_socket.recv(1) == b'0':
        print("Error: File not found in the server.")
        return

    # Get the file size to be received from the server
    received, filesize = 0, int(client_socket.recv(BUFFER).decode(FORMAT))

    # Load the progress bar
    if tqdm_available:
        progress_bar = tqdm(total=filesize, unit="B", unit_scale=True, unit_divisor=1024, desc="Receiving")

    with open(filename, "wb") as f:
        while received < filesize:
            # Read the bytes from the file until all bytes are received
            bytes_read = client_socket.recv(BUFFER)

            # Write to the file
            f.write(bytes_read)

            # Update the progress bar
            if tqdm_available:
                progress_bar.update(len(bytes_read))
            received += len(bytes_read)

    if tqdm_available:
        progress_bar.close()

    print(f"File received from Server: {filename}")

def execute_command(client_socket: socket.socket, reg: str, command: str) -> str:
    """Executes the command given by the user.

    :param socket.socket client_socket: current socket used by the client
    :param str reg: register of the client
    :param str command: command given by the user
    :return str: returns the current register/handle/alias of the client at the execution of the command
    """

    if command.startswith('/register'):
        if reg is not None:
            print("Error: Registration failed. Already registered to the server")
            return reg

        parts = command.split(" ", 1)

        if len(parts) < 2:
            print("Error: Command parameters do not match or is not allowed")
            return None

        command, handle = parts

        client_socket.sendall(command.encode(FORMAT))
        client_socket.sendall(encode_to_bytes(handle))
        client_socket.sendall(handle.encode(FORMAT))

        status = client_socket.recv(1)

        # Get the status flag, server sends a 1 if handle is valid else 0
        if status == b'1':
            print(f"Welcome {handle}!")
            return handle

        elif status == b'0':
            print("Error: Registration failed. Handle or alias already exists.")
            return None

    elif command.startswith('/store'):
        if reg is None:
            print("Error: No register entered in the server.")
            return None

        parts = command.split(" ", 1)

        if len(parts) < 2:
            print("Error: Command parameters do not match or is not allowed")
            return reg

        command, filename = parts

        if not os.path.exists(filename):
            print("Error: File not found.")
            return reg

        if not is_filename(filename):
            print(f"Error: Invalid filename {filename}.")
            return reg

        client_socket.sendall(command.encode(FORMAT))
        client_socket.sendall(encode_to_bytes(filename))
        client_socket.sendall(filename.encode(FORMAT))

        send_file(client_socket, filename)

    elif command.startswith('/get'):
        if reg is None:
            print("Error: No register entered in the server")
            return None

        parts = command.split(" ", 1)

        if len(parts) < 2:
            print("Error: Command parameters do not match or is not allowed")
            return reg

        command, filename = parts

        if not is_filename(filename):
            print(f"Error: Invalid filename {filename}.")
            return reg

        client_socket.sendall(command.encode(FORMAT))
        client_socket.sendall(encode_to_bytes(filename))
        client_socket.sendall(filename.encode(FORMAT))

        store_file(client_socket, filename)

    elif command == '/dir':
        if reg is None:
            print("Error: No register entered in the server.")
            return None

        client_socket.sendall(command.encode(FORMAT))

        # Prints the directory received from the server
        print(recv_data(client_socket).decode(FORMAT))

    elif command == '/leave':
        client_socket.sendall(command.encode(FORMAT))
        return None

    else:
        print("Error: Command not found")

    return reg

def handle_commands() -> None:
    """Handles the input given by the user

    :raises ValueError: raises this error when invalid parameters were met when inputting the command
    """
    client_socket, reg, active = None, None, False

    while True:
        command = input("Enter command: ").strip()
        print()

        if command.startswith('/join') and not active:
            try:
                _, HOST, PORT = command.split(" ", 2)
                PORT = int(PORT)

                # Check if HOST and PORT is valid
                if not is_valid_addr(HOST) or not is_valid_port(PORT):
                    raise ValueError

                # Connect to the address
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((HOST, PORT))

                # Set the active status flag to active or True
                active = True
                print("Connected to the File Exchange Server successfully!")

            except (ValueError, OSError):
                print("Error: Connection to the Server has failed! Please check IP Address and Port Number.")

        elif command == '/exit':
            print("Exiting application!")
            break # Break from the inf. loop

        # Do not allow multiple joins to different or the same server
        elif command.startswith('/join') and active:
            print("Error: Still connected to server. Leave from the server first.")

        elif command == '/?':
            print_commands()

        # Do not allow the client to leave a server if not connected
        elif not active and command == '/leave':
            print("Error: Disconnection failed. Please connect to the server first.")

        elif active:
            # Execute the command and get the register
            reg = execute_command(client_socket, reg, command)

            if reg is None and command == '/leave':
                print("Connection closed. Thank you!")
                active = False

                client_socket.close()
                client_socket = None

        # Check if the command is not in any of the active commands used
        elif any(command.startswith(key) for key in commands.keys()):
            print("Error: Command not found.")

        else:
            print("Error: Please connect to the server first")

if __name__ == "__main__":
    try:
        handle_commands()
    except ConnectionError: # Happens ie. when the server suddenly shutsdown
        print("Error: Server side connection abruptly closed")
    except KeyboardInterrupt: # Happens ie. when user accidentally used Ctrl + C on the terminal
        print("Connection closed. Thank you!")