# WARNING AI
import socket
import threading
from typing import Optional
from command_processor import CommandProcessor
from config import current_config


class IPCServer:
    def __init__(
        self,
        command_processor: CommandProcessor,
    ):
        self.command_processor = command_processor
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

    @property
    def host(self):
        return current_config.host

    @property
    def port(self):
        return current_config.port

    @host.setter
    def host(self, value):
        self._host = value

    def start(self):
        """Start the IPC server in a separate thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._run_server,
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        """Stop the IPC server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
        if self.thread:
            self.thread.join()

    def _run_server(self):
        """Main server loop."""
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )

        # Allows fast restart on Unix + Windows
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f"IPC server listening on {self.host}:{self.port}")

        try:

            self.server_socket.settimeout(.01)
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    # client_socket.settimeout(5.0)

                    threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True,
                    ).start()

                except socket.timeout:
                    continue
                except OSError:
                    if self.running:
                        continue
                    break
        finally:
            try:
                self.server_socket.close()
            except OSError:
                pass

    def _handle_client(self, client_socket: socket.socket):
        buffer = b""

        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break

                buffer += data

                while True:
                    # Step 1: read length line
                    if b"\n" not in buffer:
                        break

                    header, rest = buffer.split(b"\n", 1)

                    try:
                        length = int(header.decode("ascii"))
                    except ValueError:
                        client_socket.sendall(b"invalid\n")
                        return

                    # Step 2: wait until full payload arrives
                    if len(rest) < length:
                        break

                    payload = rest[:length]
                    buffer = rest[length:]

                    message = payload.decode("utf-8", errors="replace")

                    try:
                        response = self.command_processor.process_ipc(message)
                    except Exception:
                        response = "invalid"

                    client_socket.sendall(
                        f"{len(response)}\n".encode("ascii") +
                        response.encode("utf-8")
                    )

        except (socket.timeout, ConnectionResetError):
            pass
        finally:
            try:
                client_socket.close()
            except OSError:
                pass
