from mail_server import MailServer

# Dual SMTP+POP3 server
# change to 0.0.0.0 in docker
ip = "0.0.0.0"
# ip = "127.0.0.1"
port = 5000
try:
    print(f'starting SMTP+POP3 server on {ip}:{port}', flush=True)
    mail_server = MailServer("SMTP+POP3_BE", ip, port)
    mail_server.run()
except Exception as e:
    print(f'server error: {e}', flush=True)
