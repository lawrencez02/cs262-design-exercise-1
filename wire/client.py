from cmd import Cmd 
import queue 
import socket 
import selectors
import types 
import struct 
import threading
import sys 


# both are threadsafe 
write_queue = queue.Queue() 

sel_write = selectors.DefaultSelector() 
sel_read = selectors.DefaultSelector()

host, port = sys.argv[1], int(sys.argv[2])

# takes user input 
class UserInput(Cmd): 
    def do_login(self, login_info): 
        username, password = login_info.split(" ")
        msg = username + " " + password
        write_queue.put(struct.pack('>I', 0) + struct.pack('>I', len(msg)) + msg.encode('utf-8'))

    def do_find(self, exp): 
        write_queue.put(struct.pack('>I', 4) + struct.pack('>I', len(exp)) + exp.encode('utf-8'))
    
    def do_send(self, info): 
        send_to, msg = info.split(" ", 1)
        write_queue.put(struct.pack('>I', 2) + struct.pack('>I', len(send_to)) + send_to.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8'))
    

class Client(): 
    def __init__(self): 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(True)
        self.sock.connect((host, port))
        
    def recvall(self, n): 
        # Receive exactly n bytes from specified socket, returning None otherwise
        data = bytearray() 
        while len(data) < n: 
            packet = self.sock.recv(n - len(data))
            if not packet: 
                return None 
            data.extend(packet) 
        return data 

    def send_msg(self): 
        sel_write.register(self.sock, selectors.EVENT_WRITE)
        while True: 
            for key, mask in sel_write.select(timeout=None): 
                outb = write_queue.get()
                self.sock.sendall(outb)
    
    def receive_msg(self): 
        sel_read.register(self.sock, selectors.EVENT_READ)
        while True: 
            for key, mask in sel_read.select(timeout=None): 
                raw_opcode = self.recvall(4)
                opcode = struct.unpack('>I', raw_opcode)[0]
                if opcode == 3:
                    sentfrom_len = struct.unpack('>I', self.recvall(4))[0]
                    sentfrom = self.recvall(sentfrom_len).decode("utf-8", "strict")
                    msg_len = struct.unpack('>I', self.recvall(4))[0]
                    msg = self.recvall(msg_len).decode("utf-8", "strict")
                    print(sentfrom, ": ", msg, sep="")
                if opcode == 5:
                    result_len = struct.unpack('>I', self.recvall(4))[0]
                    result = self.recvall(result_len).decode("utf-8", "strict")
                    print(result.split(' '))
                if opcode == 6: 
                    print("You are trying to send a message to a user that doesn't exist.")


if __name__ == '__main__':
    client = Client() 
    threading.Thread(target=client.receive_msg).start()
    threading.Thread(target=UserInput().cmdloop).start()
    threading.Thread(target=client.send_msg).start()
    
    
   