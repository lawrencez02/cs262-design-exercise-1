import sys 
import socket 
import selectors
import types 
import struct 
import queue
import re

sel = selectors.DefaultSelector() 
users = {"catherine": "c", "test": "test"} # username as key and password and value
conns = {} # username as key and conn (server side connection), data as value
messages_queue = {} # who it's supposed to go to as key and a queue of (sentfrom, messages) as value
host, port = "", 12984

# create server socket
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

def recvall(sock, n): 
    data = bytearray() 
    while len(data) < n: 
        packet = sock.recv(n - len(data))
        if not packet:
            return None 
        data.extend(packet) 
    return data

def accept_wrapper(sock):   
    conn, addr = sock.accept() 
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", username="")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        raw_opcode = recvall(sock, 4)
        if not raw_opcode: 
            if data.username != '': 
                del conns[data.username]
            sel.unregister(sock)
            sock.close() 
        else: 
            opcode = struct.unpack('>I', raw_opcode)[0]
            if opcode == 0: 
                raw_msglen = recvall(sock, 4)
                msglen = struct.unpack('>I', raw_msglen)[0]
                msg = recvall(sock, msglen).decode("utf-8", "strict")
                username, password = msg.split(" ")
                if username in users and users[username] == password: 
                    # fill out conns and queue
                    data.username=username
                    conns[username] = (sock, data)
                    # messages_queue[username] = queue.Queue()
                else: 
                    print("wrong username or password - write code to deal with this later")
            if opcode == 2: # send a message 
                sendto_len = struct.unpack('>I', recvall(sock, 4))[0] 
                sendto = recvall(sock, sendto_len).decode("utf-8", "strict")
                msg_len = struct.unpack('>I', recvall(sock, 4))[0]
                msg = recvall(sock, msg_len).decode("utf-8", "strict")
                if sendto not in conns:
                    if sendto not in users: 
                        sock.sendall(struct.pack('>I', 6))
                    if sendto not in messages_queue: 
                        messages_queue[sendto] = queue.Queue()
                    messages_queue[sendto].put((data.username, msg))
                    # print("purple yams", messages_queue[sendto].get())
                else: 
                    conns[sendto][1].outb += struct.pack('>I', 3) + struct.pack('>I', len(data.username)) + data.username.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8')
            if opcode == 4: # return the list of people using wildcard or whatever 
                exp_len = struct.unpack('>I', recvall(sock, 4))[0]
                exp = recvall(sock, exp_len).decode("utf-8", "strict")
                exp_str = '.*' + exp + '.*'
                regex = re.compile(exp_str)
                result = ' '.join(list(filter(regex.match, users.keys())))
                sock.sendall(struct.pack('>I', 5) + struct.pack('>I', len(result)) + result.encode("utf-8"))

    if mask & selectors.EVENT_WRITE and data.username != '': 
        if data.username in messages_queue and not messages_queue[data.username].empty(): 
            while not messages_queue[data.username].empty(): 
                sentfrom, msg = messages_queue[data.username].get()
                sock.sendall(struct.pack('>I', 3) + struct.pack('>I', len(sentfrom)) + sentfrom.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8'))    
        if data.outb: 
            sock.sendall(data.outb)
            data.outb = data.outb[len(data.outb):]



try: 
    while True:
        # sel is monitoring lsock for a READ EVENT 
        # and the "client connection" objects for a READ or WRITE event 
        events = sel.select(timeout=None)
        for key, mask in events: 
            # from lsock 
            if key.data is None: 
                accept_wrapper(key.fileobj)
            # from one of the "client connection" objects 
            # store who you want to send the message to in key.data? 
            else: 
                service_connection(key, mask)
except KeyboardInterrupt: 
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close() 

