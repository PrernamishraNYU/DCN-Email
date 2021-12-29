import socket
from .socket_base import SocketBase

class SocketServer(SocketBase):
    SOCK_STATE_LISTENING = "listening"
    SERVER_STATE_NO_CONNECTION = "no_connection"
    SERVER_STATE_CONNECTED = "connected"
    SERVER_STATE_PROCESSING = "processing"
    connection = None
    server_state = None
    line_queue = []

    def init_socket(self):
        try:
            self.printlog(f'bind to socket on {self.ip}:{self.port}')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.ip, self.port))
            self.sock.listen()
            self.printlog(f'listening...')
            self.sock_state = self.SOCK_STATE_LISTENING
        except OSError as err:
            self.printlog(f'socket error: {err}')
            raise Exception(f'socket error: {err}')
        except ConnectionRefusedError:
            self.printlog(f'unable to init socket on {self.ip}:{self.port}')
            raise Exception(f'unable to init socket on {self.ip}:{self.port}')
        except BaseException as e:
            self.printlog(f'{e}')

    def run(self):
        self.server_state = self.SERVER_STATE_NO_CONNECTION
        while True:
            if self.sock_state == self.SOCK_STATE_CLOSED:
                self.reset()
                self.init_socket()
            else:
                self.printlog('awaiting connection...')
                connection, addr = self.sock.accept()
                self.printlog(f'connected by {addr}')
                self.connection = connection
                self.server_state = self.SERVER_STATE_CONNECTED
                # TODO: what about dual server
                self.connection_established()
                self.listen()
                self.printlog('connection closed by client.')

    def connection_established(self):
        self.printlog('NOOP connection_established')

    def reset(self):
        self.connection = None
        self.line_queue = []
        self.server_state = self.SERVER_STATE_NO_CONNECTION

    def send_message_into_connection(self, message):
        # self.printlog(f'sending message into socket: {message}')
        self.connection.sendall(message.encode('ascii'))

    def listen(self):
        line = ''
        while self.server_state != self.SERVER_STATE_NO_CONNECTION:
            newdata = self.connection.recv(4096)
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
                        if self.server_state != self.SERVER_STATE_PROCESSING:
                            self.process_next_line()

                    line = ''

    def process_next_line(self):
        if self.server_state != self.SERVER_STATE_PROCESSING and len(self.line_queue) > 0:
            self.server_state = self.SERVER_STATE_PROCESSING
            line = self.line_queue.pop(0)
            self.process_line(line)

    def process_line(self, line):
        self.printlog(f'NOOP="{line}"')
        self.line_processed()

    def line_processed(self):
        if self.server_state == self.SERVER_STATE_PROCESSING:
            self.server_state = self.SERVER_STATE_CONNECTED
