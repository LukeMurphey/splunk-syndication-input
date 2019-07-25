from BaseHTTPServer import BaseHTTPRequestHandler
import os
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

    def do_GET(self):
        
        # Handle an invalid authentication request
        if 'invalid_auth' in self.path:
            self.do_invalid_AUTHHEAD()

        # Handle an authentication request with no realm
        elif 'no_realm_auth' in self.path:
            self.do_no_realm_AUTHHEAD()

        # If a request without authentication required, then handle the file directly
        elif 'auth' not in self.path:
            with open( os.path.join("web_files", os.path.basename(self.path)), "r") as webfile:
                self.wfile.write(webfile.read())

        # Otherwise, handle an authentication request
        else:
            username = 'admin'
            password = 'changeme'
            encoded_password = base64.b64encode(username + ":" + password)
            
            ''' Present frontpage with user authentication. '''
            if self.headers.getheader('Authorization') == None:
                self.do_AUTHHEAD()
                self.wfile.write('no auth header received')
            elif self.headers.getheader('Authorization') == ('Basic ' + encoded_password):
                self.do_HEAD()
                #self.wfile.write(self.headers.getheader('Authorization'))
                #self.wfile.write('authenticated!')
                
                with open( os.path.join("web_files", os.path.basename(self.path)), "r") as webfile:
                    self.wfile.write(webfile.read())
                
                pass
            else:
                """
                print "Auth head:", self.headers.getheader('Authorization'), " did not match ", ('Basic ' + encoded_password)
                print self.headers.getheader('Authorization')[6:]
                print base64.b64decode(self.headers.getheader('Authorization')[6:])
                """
                self.do_AUTHHEAD()
                self.wfile.write(self.headers.getheader('Authorization'))
                self.wfile.write('not authenticated')
                pass
