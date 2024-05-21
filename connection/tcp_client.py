import socket

from loguru import logger


class TcpClient:

    def __init__(self, host='192.168.0.141', port=502):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))

        except Exception as e:
            logger.error(f"success failed: {e}")

    def send_message(self, message):
        if self.client_socket:
            try:
                self.client_socket.sendall(message.encode())
                logger.debug(f"message send")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    def close_connection(self):
        if self.client_socket:
            self.client_socket.close()
            logger.debug("Connection closed")
