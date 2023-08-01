from socket import socket, error, timeout, SHUT_RDWR

BUFFER_SIZE = 1024


class ClientConnection:
    @staticmethod
    def handle_command(command: str) -> None:
        pass

    def __init__(self, client_socket: socket, client_address: str, response_handler: callable) -> None:
        self.socket = client_socket
        self.address = client_address
        self.response_handler = response_handler
        self.running = False

    def handle_client(self, server_password: str) -> None:
        try:
            self.running = True
            self.socket.settimeout(360.0)  # 6 minutes to timeout.
            self.response_handler("{}:{} has connected.".format(*self.address))
            if server_password:
                client_password = self.get_data()
                if server_password != client_password:
                    self.send_data("Access denied.")
                    raise error("Access denied.")
            self.send_data("Access granted.")
            while self.running:
                data = self.get_data()
                if isinstance(data, str):
                    self.response_handler(data, "{}:{}".format(*self.address))
                    self.handle_command(data)
        except (timeout, error):
            pass
        except Exception as e:
            self.response_handler(f"Failed to handle client: {e}")
        finally:
            self.disconnect()

    def get_data(self) -> (str | None):
        try:
            data = self.socket.recv(BUFFER_SIZE)
            if data:
                return data.decode().strip()
            else:
                self.disconnect()
        except (error, timeout):
            pass
        except Exception as e:
            self.response_handler(f"Failed to get client data: {e}")
        return None

    def send_data(self, data: str) -> None:
        try:
            data = str(data).strip().encode()
            self.socket.sendall(data)
        except (error, timeout):
            pass
        except Exception as e:
            self.response_handler(f"Failed to send data to client: {e}")

    def disconnect(self) -> None:
        try:
            self.running = False
            self.socket.shutdown(SHUT_RDWR)
        finally:
            IP, PORT = self.address
            self.response_handler(f"{IP}:{PORT} was disconnected.")
            self.socket.close()