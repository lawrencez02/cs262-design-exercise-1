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

    # Pack opcode and message and send through specified socket
    def _send_msg(self, sock, opcode, msg):
        sock.sendall(struct.pack('>I', opcode) + struct.pack('>I', len(msg)) + msg.encode("utf-8"))

    # Receives n arguments from wire, packaged as len(arg1) + arg1 + len(arg2) + arg2 + ...
    def _recv_n_args(self, sock, n):
        args = []
        for _ in range(n):
            arg_len = struct.unpack('>I', self._recvall(sock, 4))[0]
            args.append(self._recvall(sock, arg_len).decode("utf-8", "strict"))
        return args

    # Accept connection from a client
    def accept_wrapper(self):
        conn, addr = self.sock.accept() 
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, outb=b"", username="")
        self.sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)

    def service_connection(self, key, mask):
        sock, data = key.fileobj, key.data
        # check if client socket has closed, unregister connection and close corresponding socket
        if mask & selectors.EVENT_READ:
            raw_opcode = self._recvall(sock, 4)
            if not raw_opcode: 
                if data.username != "": 
                    del active_conns[data.username]
                self.sel.unregister(sock)
                sock.close() 
                print(f"Closed socket with address {data.addr}")
                return
            opcode = struct.unpack('>I', raw_opcode)[0]

        # write to socket everything in message queue and data.outb first
        if mask & selectors.EVENT_WRITE and data.username != '': 
            if data.username in messages_queue and not messages_queue[data.username].empty(): 
                while not messages_queue[data.username].empty(): 
                    sentfrom, msg = messages_queue[data.username].get()
                    sock.sendall(struct.pack('>I', RECEIVE) + struct.pack('>I', len(sentfrom)) + sentfrom.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8'))    
                messages_queue.pop(data.username, None) 
            if data.outb: 
                sock.sendall(data.outb)
                data.outb = b""

        if mask & selectors.EVENT_READ:
            if opcode == LOGIN or opcode == REGISTER: # client socket is trying to login or register with a username/password
                username, password = self._recv_n_args(sock, 2)
                if data.username:
                    self._send_msg(sock, PRIVILEGE_ERROR, "You need to be logged out. Please try again!")
                    return
                if opcode == REGISTER:
                    if username in users:
                        self._send_msg(sock, REGISTER_ERROR, "Username already exists. Please try again!")
                        return
                    users[username] = password
                if username in users and users[username] == password: 
                    # fill out active_conns and queue
                    data.username = username
                    active_conns[username] = (sock, data)
                    print(f"{username} logged in successfully")
                    self._send_msg(sock, LOGIN_CONFIRM if opcode == LOGIN else REGISTER_CONFIRM, f"Logged in as {username}!")
                else: 
                    print(f"Unsuccessful login attempt by {username}")
                    self._send_msg(sock, LOGIN_ERROR, "Incorrect username or password. Please try again!")
            elif opcode == LOGOUT or opcode == DELETE:
                if not data.username:
                    self._send_msg(sock, PRIVILEGE_ERROR, "You need to be logged in. Please try again!")
                    return
                active_conns.pop(data.username, None)
                if opcode == LOGOUT:
                    self._send_msg(sock, LOGOUT_CONFIRM, "Logged out successfully!")
                    print(f"{data.username} logged out successfully")
                elif opcode == DELETE:
                    messages_queue.pop(data.username, None)
                    users.pop(data.username, None)
                    self._send_msg(sock, DELETE_CONFIRM, "Deleted account successfully!")
                    print(f"{data.username} deleted successfully")
                data.username = ''
            elif opcode == SEND: # client socket is trying to send a message
                sendto, msg = self._recv_n_args(sock, 2)
                if not data.username:
                    self._send_msg(sock, PRIVILEGE_ERROR, "You need to be logged in to send a message. Please try again!")
                    return
                if sendto not in active_conns:
                    if sendto not in users: 
                        self._send_msg(sock, SEND_ERROR, "Recipient user does not exist. Please try again!")
                    else:
                        if sendto not in messages_queue: 
                            messages_queue[sendto] = queue.Queue()
                        messages_queue[sendto].put((data.username, msg))
                else: 
                    active_conns[sendto][1].outb += struct.pack('>I', RECEIVE) + struct.pack('>I', len(data.username)) + data.username.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8')
            elif opcode == FIND: # client socket trying to find users 
                exp = self._recv_n_args(sock, 1)[0]
                regex = re.compile(exp)
                result = "Users: " + ', '.join(list(filter(regex.match, users.keys())))
                self._send_msg(sock, FIND_RESULT, result)
    
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