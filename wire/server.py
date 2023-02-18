import socket 
import selectors
import types 
import struct 
import queue
import re
from constants import *

# stores all users: username maps to password
users = {"catherine": "c", "test": "test"}
# stores all online users: username maps to (socket, data)
active_conns = {} 
# intended (offline) recipient maps to a queue of (sender, message)
messages_queue = {}
host, port = "", PORT # empty host string means server is reachable by any address it has


class Server(): 
    def __init__(self): 
        self.sel = selectors.DefaultSelector() 
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((host, port))
        lsock.listen()
        print(f"Server listening on {(host, port)}")
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)
        self.sock = lsock 
    
    # Receive exactly n bytes from specified socket, returning None otherwise
    def _recvall(self, sock, n): 
        data = bytearray() 
        while len(data) < n: 
            packet = sock.recv(n - len(data))
            if not packet:
                return None 
            data.extend(packet) 
        return data

    def accept_wrapper(self):
        conn, addr = self.sock.accept() 
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", username="")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            raw_opcode = self._recvall(sock, 4)
            # if client socket has closed, unregister connection and close corresponding server socket
            if raw_opcode is None: 
                if data.username != "": 
                    del active_conns[data.username]
                self.sel.unregister(sock)
                sock.close() 
            else: 
                opcode = struct.unpack('>I', raw_opcode)[0]
                if opcode == LOGIN: # client socket is trying to login with a username/password
                    username_len = struct.unpack('>I', self._recvall(sock, 4))[0]
                    username = self._recvall(sock, username_len).decode("utf-8", "strict")
                    password_len = struct.unpack('>I', self._recvall(sock, 4))[0]
                    password = self._recvall(sock, password_len).decode("utf-8", "strict")
                    if username in users and users[username] == password: 
                        # fill out active_conns and queue
                        data.username = username
                        active_conns[username] = (sock, data)
                        print(f"{username} logged in successfully")
                    else: 
                        print(f"Unsuccessful login attempt by {username}")
                        msg = "Incorrect username or password. Please try again!"
                        sock.sendall(struct.pack('>I', LOGIN_ERROR) + struct.pack('>I', len(msg)) + msg.encode("utf-8"))
                elif opcode == SEND: # client socket is trying to send a message
                    sendto_len = struct.unpack('>I', self._recvall(sock, 4))[0] 
                    sendto = self._recvall(sock, sendto_len).decode("utf-8", "strict")
                    msg_len = struct.unpack('>I', self._recvall(sock, 4))[0]
                    msg = self._recvall(sock, msg_len).decode("utf-8", "strict")
                    if sendto not in active_conns:
                        if sendto not in users: 
                            msg = "Recipient user does not exist. Please try again!"
                            sock.sendall(struct.pack('>I', SEND_ERROR) + struct.pack('>I', len(msg)) + msg.encode("utf-8"))
                        else:
                            if sendto not in messages_queue: 
                                messages_queue[sendto] = queue.Queue()
                            messages_queue[sendto].put((data.username, msg))
                    else: 
                        active_conns[sendto][1].outb += struct.pack('>I', RECEIVE) + struct.pack('>I', len(data.username)) + data.username.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8')
                elif opcode == FIND: # client socket trying to find users 
                    exp_len = struct.unpack('>I', self._recvall(sock, 4))[0]
                    exp = self._recvall(sock, exp_len).decode("utf-8", "strict")
                    exp_str = '.*' + exp + '.*'
                    regex = re.compile(exp_str)
                    result = ' '.join(list(filter(regex.match, users.keys())))
                    sock.sendall(struct.pack('>I', FIND_RESULT) + struct.pack('>I', len(result)) + result.encode("utf-8"))

        if mask & selectors.EVENT_WRITE and data.username != '': 
            if data.username in messages_queue and not messages_queue[data.username].empty(): 
                while not messages_queue[data.username].empty(): 
                    sentfrom, msg = messages_queue[data.username].get()
                    sock.sendall(struct.pack('>I', RECEIVE) + struct.pack('>I', len(sentfrom)) + sentfrom.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8'))    
                messages_queue.pop(data.username, None) 
            if data.outb: 
                sock.sendall(data.outb)
                data.outb = b""
    
    # main loop that runs server
    def run(self): 
        try: 
            while True: 
                events = self.sel.select(timeout=None)
                for key, mask in events: 
                    if key.data is None: 
                        self.accept_wrapper()
                    else: 
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt exception, server exiting")
        finally:
            self.sel.close()
        

if __name__ == '__main__': 
    Server().run()