from shared import SocketServer
from shared import SMTPServer
from shared import POP3Server

class MailServer(SocketServer):
   smtp_server = None
   pop3_server = None
   cur_server = None
   mode = None
   def __init__(self, name, ip, port):
       super().__init__(name, ip, port)
       self.smtp_server = SMTPServer("BE_SMTPServer", ip, port)
       self.smtp_server.set_dual_server(self)
       self.smtp_server.set_mode(SMTPServer.MODE_SAVE_TO_FILESYSTEM)
       # self.smtp_server.reset()
       self.pop3_server = POP3Server("BE_POP3Server", ip, port)
       self.pop3_server.set_dual_server(self)
       # self.pop3_server.reset()

   def reset(self):
       self.mode = None
       self.cur_server = None
       super().reset()
       # self.smtp_server.reset()
       # self.pop3_server.reset()

   def process_line(self, line):
       if not self.mode:
           self.set_mode(line)
       else:
           print(f'sending line to cur_server: {line}')
           self.cur_server.process_line(line)

       self.line_processed() 

   def set_mode(self, mode):
       if mode == "SMTP" or mode == "POP3":
           self.printlog(f'Switching into {mode} mode for connection')
           self.mode = mode
           if mode == "SMTP":
               self.cur_server = self.smtp_server
           elif mode == "POP3":
               self.cur_server = self.pop3_server

           self.cur_server.connection_established()
       else:
           print(f'Warning: unknown mode {mode} given')
           self.mode = "UNKNOWN"
