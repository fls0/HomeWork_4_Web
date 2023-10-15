from datetime import datetime
import logging
import mimetypes
import urllib.parse
import socket
import json
from pathlib import Path
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = Path()

class MyHTTPRequestHandler(BaseHTTPRequestHandler):


    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))

        clien_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clien_socket.sendto(data, ('localhost', 8080))
        clien_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

def read_data(data):
        data_parse = urllib.parse.unquote_plus(data.decode())
        try:
            parse_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            with open('storage/data.json', 'r', encoding='utf-8') as feedsjson:
                feeds = json.load(feedsjson)
                with open('storage/data.json', 'w', encoding='utf-8') as feedsjson:
                    d_now = str(datetime.now())
                    feeds[d_now] = {'username': parse_dict['username'], 'message': parse_dict['message']}
                    json.dump(feeds, feedsjson, ensure_ascii=False, indent=3)
        except ValueError as err:
            logging.error(err)
        except OSError as err:
            logging.error(err)

def run_socket_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = (host, port)
    sock.bind(server)
    try:
        while True:
            msg, address = sock.recvfrom(1024)
            logging.info(f"Socket received {address}: {msg}")
            read_data(msg)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, MyHTTPRequestHandler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=('localhost', 3000))
    server.start()

    server_socket = Thread(target=run_socket_server, args=('127.0.0.1', 8080))
    server_socket.start()
