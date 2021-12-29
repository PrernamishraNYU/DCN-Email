from flask import Flask
from flask import request
from shared import POP3Client
import socket
import html
app = Flask(__name__)

@app.route('/')
def index():
    return 'hello world'

@app.route('/email')
def email():
    try:
        email_from = request.args.get('from')
        if email_from == '':
            raise Exception() 
        from_parts = email_from.split(":")
        if len(from_parts) != 2:
            raise Exception()
        else:
            from_ip = from_parts[0]
            from_port = int(from_parts[1])
    except Exception as err:
        return f'`from` param was missing or not valid', 400
            
    print(f'connecting to POP3 server at {from_ip}:{from_port}', flush=True)
    try:
        pop3_client = POP3Client("BU_Client", from_ip, from_port)
        pop3_client.init_socket()
        messages = pop3_client.get_mail()
        if pop3_client.message_count > 0:
            resp = f'{html.escape(str(messages))}<hr>'
            i = 1
            while len(messages):
                resp = resp + f'<strong>Message {i}:</strong><div style="background-color:#ccc;border:solid 1px #999;"><pre>{html.escape(messages.pop(0))}</pre></div><br><br>'
                i = i + 1
            return resp, 200
        else:
            return f'<pre>Mailbox empty!</pre>', 200
    except Exception:
        return f'Unable to connect to POP3 server at {email_from}', 500
