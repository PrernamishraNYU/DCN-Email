from .socket_client import SocketClient

CLIENT_STATE_DUAL_SERVER_BEFORE_HANDSHAKE = "dual_server_handshake"
CLIENT_STATE_AWAITING_HANDSHAKE = "awaiting_handshake"
CLIENT_STATE_MAIL_FROM = "mail_from"
CLIENT_STATE_RCPT_TO = "rcpt_to"
CLIENT_STATE_DATA = "data"
CLIENT_STATE_MESSAGE = "message"
CLIENT_STATE_TERM_SIGNAL = "."
CLIENT_STATE_QUIT = "quit"
CLIENT_STATE_CLOSED = "closed"

class SMTPClient(SocketClient):
    connecting_to_dual_server = False
    client_state = ''
    is_error = False
    data = {}

    def set_dual_server(self):
        self.connecting_to_dual_server = True

    def process_line(self, line):
        response_code, message = self.parse_line(line)
        command = ''
        next_state = ''

        # self.printlog(f'response_code: {response_code}')
        # self.printlog(f'client_state: {self.client_state}')

        if response_code == '220' and self.client_state == CLIENT_STATE_AWAITING_HANDSHAKE:
            command = f'HELO {self.name}'
            next_state = CLIENT_STATE_MAIL_FROM

        elif response_code == '250':
            if self.client_state == CLIENT_STATE_MAIL_FROM:
                command = f"MAIL FROM: <sender@{self.data['email_from']}>"
                next_state = CLIENT_STATE_RCPT_TO
            elif self.client_state == CLIENT_STATE_RCPT_TO:
                command = f"RCPT TO: <recipient@{self.data['email_to']}>"
                next_state = CLIENT_STATE_DATA
            elif self.client_state == CLIENT_STATE_DATA:
                command = f'DATA'
                next_state = CLIENT_STATE_MESSAGE
            elif self.client_state == CLIENT_STATE_TERM_SIGNAL:
                command = f'QUIT'
                next_state = CLIENT_STATE_QUIT


        elif response_code == '354':
            if self.client_state == CLIENT_STATE_MESSAGE:
                command = self.data['email_message'] + "\n."
                next_state = CLIENT_STATE_TERM_SIGNAL

        elif response_code == '221':
            if self.client_state == CLIENT_STATE_QUIT:
                next_state = CLIENT_STATE_CLOSED
                self.printlog(f'Quit termination successful')

        elif response_code == '503':
            self.printlog(f'Server error encountered: {message}')
            command = f'QUIT'
            next_state = CLIENT_STATE_CLOSED
            is_error = True

        else:
            self.printlog(f'Unknown response code received: {response_code}')
            command = f'QUIT'
            next_state = CLIENT_STATE_CLOSED
            is_error = True

        if command:
            self.send_message_into_socket(command + '\n')
            self.client_state = next_state

        if next_state == CLIENT_STATE_CLOSED:
            self.client_state = next_state
            self.close_socket()

        self.line_processed()
 
    def parse_line(self, line):
        # SMTP server responses can be parsed programmatically
        command = line[0:3]
        line_data = line[4:]

        return (command, line_data)

    def send_message(self, email_from, email_to, email_message):
        self.printlog('Sending message...')
        self.data['email_from'] = email_from
        self.data['email_to'] = email_to
        self.data['email_message'] = email_message

        # if we're sending to a possible dual server, we need to send the protocol
        # after TCP handshake; in normal SMTP, the server initiates the state changes
        # with a 220 code, but here the client needs to send the first data into
        # the socket so the server knows which protocol to respond with
        if self.connecting_to_dual_server:
            # self.client_state = CLIENT_STATE_DUAL_SERVER_BEFORE_HANDSHAKE
            self.client_state = CLIENT_STATE_AWAITING_HANDSHAKE
            self.send_message_into_socket('SMTP\n')
        else:
            self.client_state = CLIENT_STATE_AWAITING_HANDSHAKE

        self.listen()
