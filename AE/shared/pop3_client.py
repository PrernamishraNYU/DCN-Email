from .socket_client import SocketClient

# CLIENT_STATE_DUAL_SERVER_BEFORE_HANDSHAKE = "dual_server_handshake"
CLIENT_STATE_AWAITING_HANDSHAKE = "awaiting_handshake"
CLIENT_STATE_LIST = "list"
CLIENT_STATE_RETR = "retr"
CLIENT_STATE_DELE = "data"
CLIENT_STATE_QUIT = "quit"
CLIENT_STATE_CLOSED = "closed"

class POP3Client(SocketClient):
    client_state = ''
    is_error = False
    data = {}
    message_count = 0
    message_size = {}
    message = []

    state_cur_message = 0
    state_message = ''

    def process_line(self, line):
        # print(f'process_line: {line}')
        resp, line = self.parse_line(line)
        next_state = ''
        command = ''

        if resp == "+OK":
            if self.client_state == CLIENT_STATE_AWAITING_HANDSHAKE:
                command = f'list'
                next_state = CLIENT_STATE_LIST
            elif self.client_state == CLIENT_STATE_RETR:
                # noop
                next_state = CLIENT_STATE_RETR
            elif self.client_state == CLIENT_STATE_DELE:
                self.state_cur_message = self.state_cur_message + 1
                command = f'retr {self.state_cur_message + 1}'
                next_state = CLIENT_STATE_RETR
            elif self.client_state == CLIENT_STATE_QUIT:
                next_state = CLIENT_STATE_CLOSED

        elif resp == "END":
            if self.client_state == CLIENT_STATE_LIST:
                command = f'retr {self.state_cur_message + 1}'
                next_state = CLIENT_STATE_RETR
            elif self.client_state == CLIENT_STATE_RETR:
                command = f'dele {self.state_cur_message + 1}'
                self.message.append(self.state_message)
                self.state_message = ''
                next_state = CLIENT_STATE_DELE
            elif self.client_state == CLIENT_STATE_DELE:
                next_state = CLIENT_STATE_RETR
   
        elif resp == "LINE":
            if self.client_state == CLIENT_STATE_LIST:
                parts = line.split(" ", 1)
                self.message_count = self.message_count + 1
                self.message_size[parts[0]] = int(parts[1])
            elif self.client_state == CLIENT_STATE_RETR:
                self.state_message = self.state_message + line + '\n'

        elif resp == "-ERR":
            next_state = CLIENT_STATE_CLOSED

        if next_state == CLIENT_STATE_RETR:
            if self.state_cur_message >= self.message_count:
                # we've run out of messages
                command = 'quit'
                next_state = CLIENT_STATE_QUIT

        # self.printlog(f'S: {line}')
        # self.printlog(f'next_state: {next_state}')

        if command:
            self.printlog(f'Sending next command: {command}')
            self.send_message_into_socket(command + '\n')
            self.client_state = next_state

        if next_state == CLIENT_STATE_CLOSED:
            self.client_state = next_state
            self.close_socket()

        self.line_processed()
 
    def parse_line(self, line):
        parts = line.split(' ', 1)

        if parts[0] == "+OK" or parts[0] == "-ERR":
            resp = parts[0]
        elif line[0:1] == "." and len(line) == 1:
            resp = "END"
        else:
            resp = "LINE"

        return (resp, line)

    def send_handshake(self):
        self.printlog('Sending dual server handshake')
        self.client_state = CLIENT_STATE_AWAITING_HANDSHAKE
        self.send_message_into_socket('POP3\n')
        self.listen()

    def get_mail(self):
        self.send_handshake()
        return self.message
