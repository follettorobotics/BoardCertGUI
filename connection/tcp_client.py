import socket

from loguru import logger


class TcpClient:

    def __init__(self, host='local host', port=502):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        if self.client_socket is not None:
            self.close_connection()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            logger.debug("Connected to server.")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.client_socket = None

    def send_message(self, message):
        if not self.client_socket:
            logger.warning("No connection. Attempting to reconnect...")
            self.connect()

        if self.client_socket:
            try:
                self.client_socket.sendall(message.encode())
                logger.debug("Message sent.")

                return self.client_socket.recv(1024)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.client_socket = None  # Set socket to None to trigger reconnection next time

    def close_connection(self):
        if self.client_socket:
            try:
                self.client_socket.close()
                logger.debug("Connection closed.")
            except Exception as e:
                logger.error(f"Failed to close connection: {e}")
            finally:
                self.client_socket = None
