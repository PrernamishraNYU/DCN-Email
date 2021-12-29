import os
from .socket_server import SocketServer

POP3_STATE_NOT_CONNECTED = "not_connected"
POP3_STATE_AWAITING_HANDSHAKE = "awaiting_handshake"
POP3_STATE_RECEIVING_COMMANDS = "receiving_commands"
POP3_STATE_TERM_SIGNAL = "term_signal"
# POP3_STATE_SESSION_COMPLETE = "session_complete"

SMTP_COUNT_FILE = './smtp.counter'

class POP3Server(SocketServer):
    pop3_state = POP3_STATE_NOT_CONNECTED
    current_file_count = 0
    parent_socket_server = None

    def reset(self):
        self.printlog('resetting')
        self.pop3_state = POP3_STATE_NOT_CONNECTED
        self.printlog({self.parent_socket_server})
        self.parent_socket_server.reset()

    def set_dual_server(self, parent):
        self.parent_socket_server = parent

    def send_message_into_connection(self, message):
        self.parent_socket_server.send_message_into_connection(message)

    def connection_established(self):
        self.pop3_state = POP3_STATE_AWAITING_HANDSHAKE
        self.get_file_count()
        self.send_handshake()

    def send_handshake(self):
        self.change_state(POP3_STATE_RECEIVING_COMMANDS)
        self.send_message_into_connection('+OK POP3 server ready\n')

    def change_state(self, new_state):
        self.pop3_state = new_state
      
    def process_line(self, line):
        parts = line.split(" ", 1)
        command = parts[0].lower()
        command_data = ''
        if len(parts) > 1:
            command_data = parts[1]
 
        action_func = "action_" + command
        func = getattr(self, action_func)
        responses = func(command, command_data)
        if responses:
            while len(responses) > 0:
                self.send_message_into_connection(responses.pop(0) + '\n')

        self.line_processed()
        if self.pop3_state == POP3_STATE_TERM_SIGNAL:
            self.cleanup()
            self.reset()

    def get_file_count(self):
        filename = SMTP_COUNT_FILE
        count = 0
        try:
            if os.path.exists(filename):
                fc = open(filename, "r")
                str_count = fc.read()
                if str_count != '':
                    count = int(str_count)
                fc.close()
        except OSError:
            self.printlog(f'OSError on {filename}')

        self.current_file_count = count

    def action_pop3(self, command, command_data):
        if self.pop3_state == POP3_STATE_AWAITING_HANDSHAKE:
            self.change_state(POP3_STATE_RECEIVING_COMMANDS)
            return [f'+OK POP3 server ready']
        else:
            return [f'-ERR Unknown command received: {command}']

    def action_list(self, command, command_data):
        responses = []
        success = False
        try:
            if self.current_file_count == 0:
                responses.append('+OK Mailbox is empty')
            elif self.current_file_count > 0:
                self.printlog(f'returning list for {self.current_file_count} messages')
                responses.append('+OK Mailbox scan listing follows')
                i = 1
                while i <= self.current_file_count:
                    filename = f'message_{i}.txt'
                    filesize = os.path.getsize(f'./{filename}')
                    responses.append(f'{i} {filesize}')
                    i = i + 1
            responses.append(".")
        except OSError as exp:
            responses = [f'-ERR filesystem error on POP3 server: {exp}']
        except Exception as exp:
            responses = [f'-ERR error on POP3 server: {exp}']

        return responses

    def action_retr(self, command, command_data):
        i = int(command_data)
        responses = []
        try:
            filename = f'./message_{i}.txt'
            if os.path.exists(filename):
                filesize = os.path.getsize(filename)
                self.printlog(f'retrieving file {filename}')
                responses.append(f'+OK {filesize} octets')
                fc = open(filename, "r")
                contents = fc.read()
                lines = contents.split("\n")
                while len(lines) > 0:
                    responses.append(f'{lines.pop(0)}')
                responses.append(".")
            else:
                responses.append(f'-ERR {filename} does not exist on server')
        except OSError as exp:
            responses = [f'-ERR filesystem error on POP3 server: {exp}']
        except Exception as exp:
            responses = [f'-ERR error on POP3 server: {exp}']

        return responses

    def action_dele(self, command, command_data):
        i = int(command_data)
        responses = []
        try:
            filename = f'./message_{i}.txt'
            if os.path.exists(filename):
                self.printlog(f'deleting file {filename}')
                os.remove(filename)
                responses.append('+OK Message delete')
            else:
                responses.append(f'-ERR {filename} does not exist on server')
        except OSError as exp:
            responses = [f'-ERR filesystem error on POP3 server: {exp}']
        except Exception as exp:
            responses = [f'-ERR error on POP3 server: {exp}']

        return responses

    def action_quit(self, command, command_data):
        self.change_state(POP3_STATE_TERM_SIGNAL)
        return ['+OK POP# server signing off']

    def cleanup(self):
        i = 1
        found = 0
        limit = self.current_file_count
        while i <= limit:
            filename = f'./message_{i}.txt'
            if os.path.exists(filename):
                if i != found + 1:
                    newpath = f'./message_{str(found+1)}.txt'
                    self.printlog(f'Cleanup found {filename}; moving to {newpath}')
                    os.rename(filename, newpath)
                else:
                    self.printlog(f'Cleanup found {filename}; leaving at current path')
                found = found + 1
            i = i + 1

        filename = SMTP_COUNT_FILE
        fm = open(filename, "w+")
        fm.write(str(found))
        fm.close()
        if found > 0:
            self.printlog(f'{found} messages still on server; writing count to {SMTP_COUNT_FILE}')
        else:
            self.printlog('server clean')
