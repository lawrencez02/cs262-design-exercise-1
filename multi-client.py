# multiconn-client.py

import sys
import socket
import selectors
import types
import struct

sel = selectors.DefaultSelector()
messages = [b"Message 1 from client.", b"Message 2 from client."]

host, port, num_conns = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print(f"Starting connection {connid} to {server_addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        # sel is monitoring the client socket for READ or WRITE events 
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=connid,
            msg_total=sum(len(m) for m in messages),
            recv_total=0,
            messages=messages.copy(),
            outb=b"",
        )
        sel.register(sock, events, data=data)

def recvall(sock, n): 
    data = bytearray() 
    while len(data) < n: 
        packet = sock.recv(n - len(data))
        if not packet:
            return None 
        data.extend(packet) 
    return data

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        raw_msglen = recvall(sock, 4)
        if not raw_msglen or data.recv_total == data.msg_total:
            print(f"Closing connection {data.connid}")
            sel.unregister(sock)
            sock.close()
        else: 
            msglen = struct.unpack('>I', raw_msglen)[0]
            recv_data = recvall(sock, msglen)
            print(f"Received {recv_data!r} from connection {data.connid}")
            data.recv_total += len(recv_data)
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            msg = data.messages.pop(0)
            data.outb = struct.pack('>I', len(msg)) + msg
        if data.outb: 
            print(f"Sending {data.outb!r} to connection {data.connid}")
            sent = sock.sendall(data.outb)  # Should be ready to write
            data.outb = data.outb[len(data.outb):]
            

start_connections(host, port, num_conns)
try: 
    while True:
        events = sel.select(timeout=None)
        for key, mask in events: 
            service_connection(key, mask)
except KeyboardInterrupt: 
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close() 