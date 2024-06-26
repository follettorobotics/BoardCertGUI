import socket
from Log.logger_config import logger


class TcpClient:

    def __init__(self, host='192.168.0.110', port=502):
        self.host = host
        self.port = port
        self.client_socket = None
        self.reconnected = None

    def connect(self):
        if self.client_socket is not None:
            self.close_connection()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            if self.reconnected:
                logger.info(f"재연결 완료")
                self.reconnected = False
            return True
        except Exception as e:
            logger.error(f"연결 실패: {e}")
            self.client_socket = None
        return False

    def is_connected(self):
        # Check if the socket is None or closed
        if self.client_socket is None:
            return False
        try:
            pass
        except socket.error:
            return False
        return True

    def send_message(self, message):
        if not self.is_connected():
            logger.warning("연결 에러. 재연결 시도 중...")
            self.reconnected = True
            self.connect()

        if self.client_socket:
            try:
                self.client_socket.sendall(message)

                return self.client_socket.recv(1024)
            except Exception as e:
                logger.info(f"요청 전송 실패: {e}")
                self.client_socket = None  # Set socket to None to trigger reconnection next time

    def close_connection(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception as e:
                logger.error(f"연결 종료 실패: {e}")
            finally:
                self.client_socket = None
