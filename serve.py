# python3 serve.py a 1234

import socket
import sys

types = {
    'css': 'text/css',
    'html': 'text/html',
    'ico': 'image/x-icon',
    'js': 'application/javascript'
}

def serve (folder, port):
    index = '/x.html'
    if folder.endswith('.html'):
        i = folder.rfind('/')
        if i != -1:
            index = folder[i:]
            folder = folder[:i]
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', int(port)))
    server.listen(5)
    print('localhost:' + str(port))
    while True:
        client = server.accept()[0]
        line = client.recv(4096).decode()
        line = line.split(' ')
        if len(line) == 1:
            continue
        file = line[1]
        if file[0] != '/' or file.find('..') != -1:
            continue
        file = file.replace('%20', ' ')
        type = file[file.rfind('.') + 1:]
        if type in types:
            type = types[type]
        else:
            file = index
            type = 'text/html'
        try:
            with open(folder + file, 'rb') as f:
                client.sendall(b'HTTP/1.\ncontent-type:' + type.encode() + b'\n\n' + f.read())
        except:
            next
        client.close()

serve(sys.argv[1] if len(sys.argv) > 1 else 'a', sys.argv[2] if len(sys.argv) > 2 else 1234)