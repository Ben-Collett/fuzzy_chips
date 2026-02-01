# WARNING AI
import socket
import threading
from typing import Optional
from command_processor import CommandProcessor


class IPCServer:
    def __init__(
        self,
        command_processor: CommandProcessor,
        host: str = "127.0.0.1",
        port: int = 8765,
    ):
        self.command_processor = command_processor
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

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
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
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
        """Handle a persistent client connection."""
        buffer = b""

        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    # client closed connection
                    break

                buffer += data

                # process all complete messages
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    message = line.decode("utf-8", errors="replace").strip()
                    if not message:
                        continue

                    try:
                        response = self.command_processor.process_ipc(message)
                    except Exception:
                        response = "invalid"

                    try:
                        client_socket.sendall(
                            (response + "\n").encode("utf-8")
                        )
                    except BrokenPipeError:
                        return

        except (socket.timeout, ConnectionResetError):
            pass
        finally:
            try:
                client_socket.close()
            except OSError:
                pass
