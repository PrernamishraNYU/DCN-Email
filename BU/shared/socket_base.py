import socket

class SocketBase:
    # define some states
    SOCK_STATE_CLOSED = "closed"
    sock = None
    sock_state = None
    log_indent = 0
    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
        self.sock_state = self.SOCK_STATE_CLOSED

    def set_indent(self, indent):
        self.log_indent = indent

    def printlog(self, message):
        print(f'{self.log_indent * "    "}[{self.name}]: {message}', flush=True)
       
