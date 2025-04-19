# CSNETWK_MP 
A Python application that provides a file transfer client-server system that supports basic operations such as connecting to a server, registering a user, and sending/receiving files with real-time progress indication if tqdm was installed.

## Testers
The project includes the ff. files for testing:
- robot.png (~300KB)
- pins.jpg (~700KB)
- test.txt (~55MB)

## Dependencies
The project has the ff. Python packages:

- **tqdm**: A library for displaying progress bars. (Optional)

### Installing Dependencies
To install the required dependency, run the following command:

```bash
pip install tqdm
```

**If `pip` is not installed**, you can install it using the ff. steps:

1. Ensure Python is installed on your system.

2. Run the following command to install `pip`:
   ```bash
   python -m ensurepip --upgrade
   ```

3. Once `pip` is installed, use it to install `tqdm`:
   ```bash
   pip install tqdm
   ```

### Verifying Installation
To verify that `tqdm` is installed, you can run:
```bash
pip show tqdm
```

### Difficulty in installing dependency
If you cannot install `tqdm` package, the program can still run without the ``tqdm`` package.

## Running the Server and Client Applications
To run the server and client applications, use the ff. commands:

### 1. Running the Server
- **Default host IP and port (5050):**
```bash
py .\SERVER.py
```

- **Custom IP and port:**
```bash
py .\SERVER.py <ip_addr> <port_number>
```

### 2. Running the Client Application
```bash
py .\CLIENT.py
```
