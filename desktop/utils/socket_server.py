from socket import socket, error, timeout, SOCK_STREAM, SOCK_DGRAM, AF_INET
from concurrent.futures import ThreadPoolExecutor
from random import randint
from re import match
import pyautogui

BUFFER_SIZE = 1024


class SocketServer:
    @staticmethod
    def retrieve_data(client: socket) -> (str | None):
        try:
            data = client.recv(BUFFER_SIZE)
            return data.decode().strip()
        except:
            return None

    @staticmethod
    def send_data(client: socket, data: str) -> bool:
        try:
            data = str(data).strip().encode()
            client.sendall(data)
            return True
        except:
            return False

    @staticmethod
    def get_private_ip() -> str:
        try:
            with socket(AF_INET, SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                private_ip = s.getsockname()[0]
            return str(private_ip).strip()
        except error as e:
            print(f"Unable to retrieve private IP: {e}")
            return "127.0.0.1"

    @staticmethod
    def generate_port() -> int:
        try:
            return randint(1024, 65535)
        except error as e:
            print(f"Failed to generate a random port: {e}")
            return 12345

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        ip_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        return match(ip_pattern, ip) is not None

    @staticmethod
    def is_valid_port(port: str) -> bool:
        return 1024 <= int(port) <= 65535

    def __init__(self, response_handler: callable) -> None:
        self.response_handler = response_handler
        self.server_socket = None
        self.running = False
        self.clients = []

    def start(self, host: str, port: str, password: str, max_connections: str) -> None:
        try:
            if self.running:
                raise RuntimeError("Server is already running!")
            elif not self.is_valid_ip(host):
                raise ValueError("Invalid host IP address.")
            elif not port.isdigit():
                raise ValueError("Port must be a valid integer number.")
            port = int(port)
            if not self.is_valid_port(port):
                raise ValueError("Port must be in the range 1024 to 65535.")
            elif not max_connections.isdigit():
                raise ValueError("Max connections must be a integer number.")
            max_connections = int(max_connections)
            if max_connections <= 0:
                raise ValueError("Max connections must be higher than 0.")
            self.server_socket = socket(AF_INET, SOCK_STREAM)
            self.server_socket.bind((host, port))
            self.server_socket.listen(max_connections)
            with ThreadPoolExecutor(max_connections) as executor:
                self.response_handler(f"Server listening on {host}:{port}.")
                self.running = True
                while self.running:
                    client, address = self.server_socket.accept()
                    self.clients.append(client)
                    executor.submit(
                        self.handle_client,
                        client,
                        address,
                        password
                    )
        except (error, timeout):
            pass
        except Exception as e:
            self.response_handler(f"Unable to start server: {e}")

    def handle_client(self, client: socket, address: tuple, server_password: str) -> None:
        try:
            self.response_handler("{}:{} has connected.".format(*address))
            if server_password:
                password = self.retrieve_data(client)
                if password != server_password:
                    self.send_data(client, "Access denied.")
                    raise error
            self.send_data(client, "Access granted.")
            while self.running:
                commands = self.retrieve_data(client)
                if not commands:
                    break
                for command in commands.split("\n"):
                    command = command.strip()
                    if not command:
                        continue
                    self.handle_command(command)
        except (error, timeout):
            pass
        except Exception as e:
            self.response_handler(f"Failed to handle client: {e}")
        finally:
            client.close()
            self.response_handler("{}:{} was disconnected.".format(*address))

    def handle_command(self, command: str):
        try:
            print(command)
        except Exception as e:
            self.response_handler(f"Failed to handle command: {e}")

    def stop(self, force_stop: bool = False) -> None:
        try:
            if force_stop:
                self.response_handler = lambda *arguments: None
            elif not self.running:
                raise RuntimeError("Server is not running!")
            self.running = False
            for client in self.clients:
                self.send_data(client, "")
                client.close()
                self.clients.pop(0)
            if self.server_socket:
                self.server_socket.close()
            self.server_socket = None
            if not force_stop:
                self.response_handler("Server isn't listening anymore.")
        except (error, timeout):
            pass
        except Exception as e:
            if not force_stop:
                self.response_handler(f"Unable to stop server: {e}")
