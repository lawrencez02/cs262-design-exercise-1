import sys 
import socket 
import selectors
import types 
import struct 

sel = selectors.DefaultSelector() 

# setting the host and port to be first, second command line arguments respectively 
host, port = sys.argv[1], int(sys.argv[2])
# same as with single client server 
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
# calls to this server will no longer block 
# calls to server return immediately, user isn't "blocked" until call returns
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

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
    # either lsock or client connection obj receives something ready to read 
    if mask & selectors.EVENT_READ:
        raw_msglen = recvall(sock, 4)
        if not raw_msglen: 
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
        else:
            msglen = struct.unpack('>I', raw_msglen)[0]
            recv_data = recvall(sock, msglen)
            data.outb += recv_data
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            data.outb = struct.pack('>I', len(data.outb)) + data.outb
            sent = sock.sendall(data.outb)  # Should be ready to write
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
            else: 
                service_connection(key, mask)
except KeyboardInterrupt: 
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close() 