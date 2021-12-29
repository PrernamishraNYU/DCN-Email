import socket
from flask import Flask
from flask import request
from shared import SMTPClient
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

        email_to = request.args.get('to')
        if email_to == '':
            raise Exception() 
        to_parts = email_to.split(":")
        if len(to_parts) != 2:
            raise Exception()
        else:
            to_ip = to_parts[0]
            to_port = int(to_parts[1])

        email_message = request.args.get('message')
    except Exception as err:
        return f'`from` or `to` param was missing or not valid', 400

    try:
        smtp_client = SMTPClient("Client_AU", from_ip, from_port)
        smtp_client.init_socket()
        smtp_client.send_message(email_from, email_to, email_message)
        if not smtp_client.is_error:
            return f'Message sent!<br>\n<br>\nFrom: {email_from}<br>\nTo: {email_to}<br>\nMessage:<br>\n{email_message}\n<br>', 200
        else:
            return f'Message was not sent', 500
    except OSError as msg:
        return f'Socket error: {msg}', 500
    except ConnectionRefusedError:
        return f'Unable to connect to SMTP server at {email_from}', 500
    except Exception as e:
        return f'Error sending message ({e})', 500
