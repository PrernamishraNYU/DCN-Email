import re
import os
from datetime import datetime
from .socket_server import SocketServer
from .smtp_client import SMTPClient

SMTP_STATE_NOT_CONNECTED = "not_connected"
SMTP_STATE_CONNECTED = "send_handshake"
SMTP_STATE_AWAITING_HANDSHAKE_RESPONSE = "awaiting_handshake_response"
SMTP_STATE_RECEIVING_HEADERS = "receiving_headers"
SMTP_STATE_RECEIVING_MESSAGE = "receiving_message"
SMTP_STATE_TERM_SIGNAL = "term_signal"
SMTP_STATE_TRANSACTION_COMPLETE = "transaction_complete"
SMTP_STATE_SHUTDOWN_SEQUENCE = "shutdown_sequence"

class SMTPServer(SocketServer):
    MODE_SEND_VIA_SMTP = "send_via_smtp"
    MODE_SAVE_TO_FILESYSTEM = "save_to_filesystem"
    mode = None
    smtp_state = SMTP_STATE_NOT_CONNECTED
    connection = None
    dual_server = False
    data = {}

    parent_socket_server = None

    def reset(self):
        self.smtp_state = SMTP_STATE_NOT_CONNECTED
        if self.dual_server:
            self.parent_socket_server.reset()
        else:
            super().reset()

    def connection_established(self):
        self.smtp_state = SMTP_STATE_CONNECTED
        self.send_handshake()

    def set_dual_server(self, parent):
        self.dual_server = True
        self.parent_socket_server = parent

    def send_message_into_connection(self, message):
        if self.dual_server:
            self.parent_socket_server.send_message_into_connection(message)
        else:
            super().send_message_into_connection(message)

    def send_handshake(self):
        response = self.action_send_handshake('', '')
        self.send_message_into_connection(response + '\n')
        self.change_state(SMTP_STATE_AWAITING_HANDSHAKE_RESPONSE)

    def set_mode(self, mode):
        if mode == self.MODE_SEND_VIA_SMTP or mode == self.MODE_SAVE_TO_FILESYSTEM:
            self.mode = mode

    def change_state(self, new_state):
        if new_state == SMTP_STATE_RECEIVING_HEADERS:
            self.data['email_from'] = ''
            self.data['email_to'] = ''
            self.data['parsed_from'] = {}
            self.data['parsed_to'] = {}
            self.data['email_message'] = ''

        self.smtp_state = new_state
      
    def process_line(self, line):
        command, line_data = self.parse_line(line)
        action_func = "action_" + self.smtp_state
        func = getattr(self, action_func)
        response = func(command, line_data)
        if response != None:
             self.send_message_into_connection(response + '\n')

        self.line_processed()
        if self.smtp_state == SMTP_STATE_SHUTDOWN_SEQUENCE:
            self.reset()
 
    def parse_line(self, line):
        # first parse the SMTP commands manually since they are variable length
        # with optional spaces and terminating colon character :-\
        command = ''
        line_data = ''
        if line[0:4] == "HELO":
            command = "HELO"
            line_data = line[5:]
        elif line[0:10] == "MAIL FROM:":
            command = "MAIL_FROM"
            line_data = line[11:]
        elif line[0:8] == "RCPT TO:":
            command = "RCPT_TO"
            line_data = line[9:]
        elif line[0:4] == "DATA":
            command = "DATA"
        elif line[0:1] == "." and len(line) == 1:
            command = "TERM_SIGNAL"
        elif line[0:4] == "QUIT":
            command = "QUIT"
        else:
            command = "LINE"
            line_data = line
  
        return (command, line_data)

    def action_send_handshake(self, command, line_data):
        if self.smtp_state == SMTP_STATE_CONNECTED:
            return f'220 {self.name}'
        else:
            return f'503 connection error'

    def action_awaiting_handshake_response(self, command, line_data):
        if self.smtp_state == SMTP_STATE_AWAITING_HANDSHAKE_RESPONSE:
            if command == 'HELO':
                self.data['email_server'] = line_data
                self.change_state(SMTP_STATE_RECEIVING_HEADERS)
                return f"250 Hello {self.data['email_server']}, pleased to meet you"
            else:
                return f'503 Expecting HELO, received {command}'
        else:
            return f'503 SMTP server entered bad state'

    def action_receiving_headers(self, command, line_data):
        if self.smtp_state == SMTP_STATE_RECEIVING_HEADERS:
            if command == 'MAIL_FROM':
                self.data['email_from'] = line_data
                self.data['parsed_from'] = self.parse_email_from()
                return f"250 {self.data['email_from']} ... Sender ok"
            elif command == 'RCPT_TO':
                self.data['email_to'] = line_data
                self.data['parsed_to'] = self.parse_email_to()
                return f"250 {self.data['email_to']} ... Recipient ok"
            elif command == "DATA":
                if not self.data['email_from'] or not self.data['email_to']:
                    return f"503 Sender or recipient not specified (sender={self.data['email_from']}, recipient={self.data['email_to']}"
                else:
                    self.change_state(SMTP_STATE_RECEIVING_MESSAGE)
                    return f'354 Enter mail, end with "." on a line by itself'
            else:
                return f'503 Expecting MAIL FROM or RCPT TO, received {command}'
        else:
            return f'503 SMTP server entered bad state'

    def action_receiving_message(self, command, line_data):
        # print(f'in func: {command}, {line_data}')
        # print(f'state in func: {self.smtp_state}')
        if self.smtp_state == SMTP_STATE_RECEIVING_MESSAGE:
            if command == 'LINE':
                self.data['email_message'] = self.data['email_message'] + line_data + '\n'
            elif command == 'TERM_SIGNAL':
                self.change_state(SMTP_STATE_TERM_SIGNAL)
                ## write to filesystem or send message here
                success = False
                error_message = ''
                if self.mode == self.MODE_SEND_VIA_SMTP:
                    # self.printlog(f"message to send: {self.data['email_message']}")
                    success = self.send_via_smtp()
                    if not success:
                        error_message = f"503 server failed to send to SMTP client at {self.data['parsed_to'].ip}:{self.data['parsed_to'].port}"
                
                elif self.mode == self.MODE_SAVE_TO_FILESYSTEM:
                    success = self.save_to_filesystem()
                    if not success:
                        error_message = f"503 server failed to save message to filesystem"

                if success:
                    self.change_state(SMTP_STATE_TRANSACTION_COMPLETE)
                    return f'250 Message accepted for delivery'
                else:
                    return error_message

            else:
                return f'503 SMTP server entered bad state during receiving message phase'
        else:
            return f'503 SMTP server entered bad state'

    #def action_term_signal(self, command, line_data):
    #    self.close_connection()

    def action_transaction_complete(self, command, line_data):
        if self.smtp_state != SMTP_STATE_RECEIVING_MESSAGE:
            if command == "QUIT":
                self.change_state(SMTP_STATE_SHUTDOWN_SEQUENCE)
                return f'221 {self.name} closing connection'
            else:
                return f'503 expecting QUIT signal, received {command}'
        else:
            return f'503 SMTP server entered bad state after message received'

    def save_to_filesystem(self):
        success = False
        try:
            filename = './smtp.counter'
            count = 0
            if os.path.exists(filename):
                fc = open(filename, "r+")
                str_count = fc.read()
                if str_count != '':
                    count = int(str_count)
                fc.close()

            new_count = count + 1
            self.printlog(f"Messages currently on system: {count}")
            today = datetime.now()
            formatted = today.strftime("%Y-%m-%d %H:%M:%S")
            # print(f"email_from: {self.data['email_from']}")
            # print(f"email_to: {self.data['email_to']}")
            # print(f"message: {self.data['email_message']}")
            message = f"From: {self.data['email_from']}\nTo: {self.data['email_to']}\nDate: {formatted}\n\n{self.data['email_message']}"
            self.printlog(f"Writing email message #{new_count}:\n{message}")

            msg_filename = f'./message_{new_count}.txt'
            fm = open(msg_filename, "w+")
            fm.write(message)
            fm.close()
            fc = open(filename, "w")
            fc.write(str(new_count))
            fc.close()
            self.printlog(f"Message saved to filesystem!")
            success = True
        except Exception as exp:
            self.printlog(f"Filesystem i/o error: {exp}")

        return success

    def send_via_smtp(self):
        self.printlog("sending message via SMTP")
        success = False
        try:
            addr = self.data['parsed_to']
            # print(f'{addr}')
            self.printlog(f"connecting to SMTP server at {addr['ip']}:{addr['port']}")
            email_from_raw = self.data['parsed_from']['ip'] + ":" + str(self.data['parsed_from']['port'])
            email_to_raw = self.data['parsed_to']['ip'] + ":" + str(self.data['parsed_to']['port'])
            ### print(f"SMTP SERVER TO CLIENT MESSAGE: {self.data['email_message']}")
            smtp_client = SMTPClient("Client_AE", addr['ip'], addr['port'])
            smtp_client.set_indent(self.log_indent + 1)
            smtp_client.init_socket()
            smtp_client.set_dual_server()
            smtp_client.send_message(email_from_raw, email_to_raw, self.data['email_message'])
            if not smtp_client.is_error:
                self.printlog("Message sent!")
                success = True
            else:
                self.printlog(f'SMTPClient error')
        except ConnectionRefusedError:
            self.printlog(f"Unable to connect to SMTP server at {addr['ip']}:{addr['port']}")

        # self.printlog(f'SUCCESS: {success}')
        return success

    def parse_email_from(self):
        return self.parse_ip_port(self.data['email_from'])

    def parse_email_to(self):
        return self.parse_ip_port(self.data['email_to'])

    def parse_ip_port(self, addr):
        res = re.search(r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]):([0-9]{2,6})', addr)
        if res and res.group(1) and res.group(2):
            return {'ip': res.group(1), 'port': int(res.group(2))}
        return {}

