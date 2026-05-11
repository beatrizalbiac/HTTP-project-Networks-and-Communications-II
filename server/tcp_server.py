import socket
import threading
from http_parser import HTTPParser
from http_response import HTTPResponse
from router import Router
from logger import logger

_CHUNKED_THRESHOLD = 512

class TCPServer:
    def __init__(self, router: Router, host: str, port: int):
        self.router = router
        self.host = host
        self.port = port

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(50)
        logger.info(f"Server listening on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = server_socket.accept()
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr),
                    daemon=True
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("Server stopped")
        finally:
            server_socket.close()

    def _handle_connection(self, conn: socket.socket, addr):
        logger.debug(f"New connection from {addr}")
        try:
            while True:
                raw = self._recv_full_request(conn)
                if not raw:
                    break

                request = HTTPParser.parse(raw)
                if request is None:
                    response = HTTPResponse.bad_request("Could not parse request")
                    logger.warning(f"Could not parse request from {addr}")
                else:
                    response = self.router.dispatch(request)
                    logger.info(f"{request.method} {request.path} → {response.status}")

                use_chunked = len(response.body) > _CHUNKED_THRESHOLD
                
                conn.sendall(response.to_bytes(use_chunked=use_chunked))

                connection_header = ""
                if request:
                    connection_header = request.header("connection") or ""
                if connection_header.lower() == "close":
                    break

        except (ConnectionResetError, BrokenPipeError):
            logger.debug(f"Client {addr} disconnected")
        except Exception as e:
            logger.error(f"Error handling connection from {addr}: {e}", exc_info=True)
        finally:
            conn.close()
            logger.debug(f"Connection to {addr} closed")

    def _recv_full_request(self, conn: socket.socket) -> bytes:
        buffer = b""
        conn.settimeout(30.0)

        try:
            while b"\r\n\r\n" not in buffer:
                chunk = conn.recv(4096)
                if not chunk:
                    return b""
                buffer += chunk

            header_part, _, body_part = buffer.partition(b"\r\n\r\n")

            content_length = 0
            for line in header_part.split(b"\r\n")[1:]:
                if line.lower().startswith(b"content-length:"):
                    content_length = int(line.split(b":")[1].strip())
                    break

            while len(body_part) < content_length:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                body_part += chunk

            return header_part + b"\r\n\r\n" + body_part

        except socket.timeout:
            return b""