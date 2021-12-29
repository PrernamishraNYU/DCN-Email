import socket
from shared import SMTPServer

# SMTP server
# change to 0.0.0.0 in docker
ip = "0.0.0.0"
# ip = "127.0.0.1"
port = 4000
try:
    print(f'starting SMTP server on {ip}:{port}', flush=True)
    smtp_server = SMTPServer("Server_AE", ip, port)
    smtp_server.set_mode(SMTPServer.MODE_SEND_VIA_SMTP)
    smtp_server.run()
except Exception as e:
    print(f'server error: {e}', flush=True)
