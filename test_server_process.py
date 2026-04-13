
import socket
from io import StringIO
from unittest.mock import patch

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(='', 8080)
sock.setblocking(False)

def start_server():
    global server_thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    sock.close()

sock.listen(5)
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()
time.sleep(1)

import requests
response = requests.get('http://localhost:8080/', timeout=5)
print(f'HTTP Status: {response.status_code}')
print(f'HEADERS: {dict(response.headers)}')
print(f'Body: {response.text}')
