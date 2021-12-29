import socket
from .socket_base import SocketBase

class SocketClient(SocketBase):
    SOCK_STATE_CONNECTED = "connected"
    SOCK_STATE_PROCESSING = "processing"
    SOCK_STATE_CLOSED = "closed"
    line_queue = []
    def init_socket(self):
        try:
            self.printlog(f'connecting to socket on {self.ip}:{self.port}')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
            self.printlog(f'connected')
            self.sock_state = self.SOCK_STATE_CONNECTED
        except OSError as err:
            self.printlog(f'socket error: {err}')
            raise Exception(f'socket error: {err}')
        except ConnectionRefusedError:
            self.printlog(f'unable to init socket on {self.ip}:{self.port}')
            raise Exception(f'unable to init socket on {self.ip}:{self.port}')
        except BaseException as e:
            self.printlog(f'{e}')

    def close_socket(self):
        self.printlog(f'closing client socket')
        self.sock_state = self.SOCK_STATE_CLOSED
        self.sock.close()

    def send_message_into_socket(self, message):
        # self.printlog(message)
        self.sock.sendall(message.encode('ascii'))

    def listen(self):
        line = ''
        while self.sock_state != self.SOCK_STATE_CLOSED:
            # print('listening on sock')
            newdata = self.sock.recv(4096)
            if newdata:
                line = line + newdata.decode('ascii')
                if line[-1] == "\n":
                    all_lines = line.split("\n")
                    # the last element should be a blank string
                    all_lines.pop()
                    while len(all_lines) > 0:
                        this_line = all_lines.pop(0)
                        self.printlog(f'RECV_LINE="{this_line}"')
                        self.line_queue.append(this_line)
                        if self.sock_state != self.SOCK_STATE_PROCESSING:
                            self.process_next_line()

                    line = ''

    def process_next_line(self):
        # print('process_next_line')
        # print(f'total queue length: {len(self.line_queue)}')
        if self.sock_state != self.SOCK_STATE_PROCESSING and len(self.line_queue) > 0:
            self.sock_state = self.SOCK_STATE_PROCESSING
            line = self.line_queue.pop(0)
            # print(f'line: {line}')
            self.process_line(line)

    def process_line(self, line):
        self.printlog(f'NOOP')
        self.line_processed()

    def line_processed(self):
        # print(f'line processed (state now: {self.sock_state})')
        if self.sock_state == self.SOCK_STATE_PROCESSING:
            self.sock_state = self.SOCK_STATE_CONNECTED
