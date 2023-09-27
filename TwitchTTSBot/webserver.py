from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse
from typing import Any
import ssl

class http_server:
    # @param arg: Argument for the BaseHTTPRequestHandler
    # @param port: website port
    # @param only_local: Listen only for localhost (True), or listen all interfaces (False)
    def __init__(self, arg: Any, port: int = 7890, only_local: bool = False):
        def handler(*args):
            AudioServerWebsite(arg, *args)
        server = HTTPServer(('localhost' if only_local else '', port), handler)
        # HTTPS
        server.socket = ssl.wrap_socket(server.socket,
                                        server_side=True,
                                        certfile="server.pem",
                                        keyfile="key.pem",
                                        ssl_version=ssl.PROTOCOL_TLS)
        server.serve_forever()

class AudioServerWebsite(BaseHTTPRequestHandler):
    def __init__(self, secret_token: str = 'admin', *args):
        self._secret_token = secret_token
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        parsed_path = parse.urlsplit(self.path)
        get_params = dict(parse.parse_qsl(parsed_path.query))
        #print(get_params)

        if not 'token' in get_params or get_params['token'] != self._secret_token:
            self.send_response(401)
            self.end_headers()
            return
            
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

def start(secret_token: str = 'admin', port: int = 7890, only_local: bool = False):
    http_server(secret_token, port, only_local)

if __name__ == '__main__':
    start()