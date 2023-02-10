from test_web_server import TestWebServerHandler

try:
    from SocketServer import TCPServer
except:
    from socketserver import TCPServer

def start_server():
    httpd = TCPServer(("", 8888), TestWebServerHandler)
    httpd.serve_forever()

start_server()
