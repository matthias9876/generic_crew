
#!/usr/bin/env python3

# server.py - Python HTTP server using only standard library

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class GATHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'')
            if self.path.endswith('.html'):
                import json
                from datetime import datetime
                data = {"timestamp": datetime.now().isoformat()[:19]}
            else:
                import json
                # Check for index.json
                try:
                    with open('/index.json', 'r') as f:
                        data = json.load(f)
                except:
                    data = {"timestamp": datetime.now().isoformat()[:19]}
            self.wfile.write(json.dumps(data).encode())
        elif self.path == '/index.json':
            with open('/index.json', 'r') as f:
                data = json.load(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK: Server is running')
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), GATHandler)
    print(f'Starting server on port {port}...')
    server.serve_forever()
