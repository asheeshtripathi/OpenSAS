from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import server as sas
from io import BytesIO

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'SAS Emulation HTTPS server')

    def do_POST(self):
        if (self.path == "/sas-api/registration"):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            sas_resp = sas.register('', body)
            # response.write(b'This is POST request. ')
            # response.write(b'Received: ')
            print(sas_resp)
            response.write(str.encode(sas_resp))
            self.wfile.write(response.getvalue())
        if (self.path == "/sas-api/spectrumInquiry"):
            print("Spectrum Inquiry")
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            sas_resp = sas.spectrumInquiryRequest('', body)
            # response.write(b'This is POST request. ')
            # response.write(b'Received: ')
            print(sas_resp)
            response.write(str.encode(sas_resp))
            self.wfile.write(response.getvalue())
        if (self.path == "/sas-api/grant"):
            print("Grant")
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            sas_resp = sas.grantRequest('', body)
            # response.write(b'This is POST request. ')
            # response.write(b'Received: ')
            print(sas_resp)
            response.write(str.encode(sas_resp))
            self.wfile.write(response.getvalue())
        if (self.path == "/sas-api/heartbeat"):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            sas_resp = sas.heartbeat('', body)
            # response.write(b'This is POST request. ')
            # response.write(b'Received: ')
            print(sas_resp)
            response.write(str.encode(sas_resp))
            self.wfile.write(response.getvalue())
        if (self.path == "/sas-api/relinquishment"):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            sas_resp = sas.relinquishment('', body)
            # response.write(b'This is POST request. ')
            # response.write(b'Received: ')
            print(sas_resp)
            response.write(str.encode(sas_resp))
            self.wfile.write(response.getvalue())
        if (self.path == "/sas-api/deregistration"):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            sas_resp = sas.deregister('', body)
            # response.write(b'This is POST request. ')
            # response.write(b'Received: ')
            print(sas_resp)
            response.write(str.encode(sas_resp))
            self.wfile.write(response.getvalue())
        

httpd = HTTPServer(('localhost', 1443), SimpleHTTPRequestHandler)

httpd.socket = ssl.wrap_socket (httpd.socket, 
        keyfile="Certs/myCA.key", 
        certfile='Certs/myCA.pem', server_side=True)
print("Listening on port 1443")
httpd.serve_forever()

