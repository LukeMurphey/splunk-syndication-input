try:
    from BaseHTTPServer import BaseHTTPRequestHandler
except:
    from http.server import BaseHTTPRequestHandler

import os
import sys
import base64

class TestWebServerHandler(BaseHTTPRequestHandler):
    ''' Main class to present webpages and authentication. '''
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_no_realm_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
    def do_invalid_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'basi')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def read_bytes(self, webfile):
        """
        If this is on Python 3, we need to decode the file into bytes.
        """
        if sys.version_info.major >= 3:
            return bytearray(webfile.read(), 'utf-8')
        else:
            return webfile.read()

    def str_to_bytes(self, s):
        if sys.version_info.major >= 3:
            return bytearray(s, 'utf-8')
        else:
            return s    

    def get_header(self, header):
        if hasattr(self.headers, 'getheader'):
            return self.headers.getheader(header)
        else:
            return self.headers.get(header)

    def do_GET(self):
        
        # Handle an invalid authentication request
        if 'invalid_auth' in self.path:
            self.do_invalid_AUTHHEAD()

        # Handle an authentication request with no realm
        elif 'no_realm_auth' in self.path:
            self.do_no_realm_AUTHHEAD()

        # If a request without authentication required, then handle the file directly
        elif 'auth' not in self.path:
            self.do_HEAD()
            with open( os.path.join("web_files", os.path.basename(self.path)), "r") as webfile:
                self.wfile.write(self.read_bytes(webfile))

        # Otherwise, handle an authentication request
        else:
            username = 'admin'
            password = 'changeme'
            encoded_password = base64.b64encode(self.str_to_bytes(username + ":" + password))
            
            ''' Present frontpage with user authentication. '''
            if self.get_header('Authorization') == None:
                self.do_AUTHHEAD()
                self.wfile.write('no auth header received')
            elif self.get_header('Authorization') == ('Basic ' + encoded_password):
                self.do_HEAD()
                #self.wfile.write(self.get_header('Authorization'))
                #self.wfile.write('authenticated!')
                
                with open( os.path.join("web_files", os.path.basename(self.path)), "r") as webfile:
                    self.wfile.write(self.read_bytes(webfile))
                
                pass
            else:
                """
                print "Auth head:", self.get_header('Authorization'), " did not match ", ('Basic ' + encoded_password)
                print self.get_header('Authorization')[6:]
                print base64.b64decode(self.get_header('Authorization')[6:])
                """
                self.do_AUTHHEAD()
                self.wfile.write(self.get_header('Authorization'))
                self.wfile.write('not authenticated')
                pass
