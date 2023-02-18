from cmd import Cmd 
import queue 
import socket 
import selectors
import struct 
import threading
import sys 
from constants import *


# thread-safe queue for outgoing messages from client
write_queue = queue.Queue() 
# selector used by client's write thread to know when socket is writable
sel_write = selectors.DefaultSelector() 
# selector used by client's read thread to know when socket is readable
sel_read = selectors.DefaultSelector()

host, port = sys.argv[1], int(sys.argv[2])


# takes and parses command-line user input for all different commands
class UserInput(Cmd): 
    def do_login(self, login_info): 
        login_info = login_info.split()
        if len(login_info) != 2:
            print("Incorrect arguments: correct form is login [username] [password]. Please try again!")
            return
        username, password = login_info
        if '.' in username or '*' in username:
            print("Characters '.' and '*' not allowed in usernames. Please try again!")
            return
        if len(username) >= MAX_NAME_PASS_LEN or len(password) >= MAX_NAME_PASS_LEN:
            print("Username or password is too long. Please try again!")
            return
        write_queue.put(struct.pack('>I', LOGIN) + struct.pack('>I', len(username)) + username.encode('utf-8') + struct.pack('>I', len(password)) + password.encode('utf-8'))

    def do_find(self, exp): 
        write_queue.put(struct.pack('>I', FIND) + struct.pack('>I', len(exp)) + exp.encode('utf-8'))
    
    def do_send(self, info): 
        info = info.split(' ', 1)
        if len(info) != 2:
            print("Incorrect arguments: correct form is send [username] [message]. Please try again!")
            return
        send_to, msg = info
        write_queue.put(struct.pack('>I', SEND) + struct.pack('>I', len(send_to)) + send_to.encode('utf-8') + struct.pack('>I', len(msg)) + msg.encode('utf-8'))
    

class Client(): 
    def __init__(self): 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(True)
        self.sock.connect((host, port))
    
    # Receive exactly n bytes from server, returning None otherwise
    def _recvall(self, n): 
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
                raw_statuscode = self._recvall(4)
                statuscode = struct.unpack('>I', raw_statuscode)[0]
                if statuscode == RECEIVE:
                    sentfrom_len = struct.unpack('>I', self._recvall(4))[0]
                    sentfrom = self._recvall(sentfrom_len).decode("utf-8", "strict")
                    msg_len = struct.unpack('>I', self._recvall(4))[0]
                    msg = self._recvall(msg_len).decode("utf-8", "strict")
                    print(sentfrom, ": ", msg, sep="")
                elif statuscode in [LOGIN_ERROR, FIND_RESULT, SEND_ERROR]:
                    msg_len = struct.unpack('>I', self._recvall(4))[0]
                    msg = self._recvall(msg_len).decode("utf-8", "strict")
                    print(msg.split(' ') if statuscode == FIND_RESULT else msg)


if __name__ == '__main__':
    # instantiate client and run separate threads for command-line input, sending messages, and receiving messages
    client = Client() 
    threading.Thread(target=client.receive_msg).start()
    threading.Thread(target=UserInput().cmdloop).start()
    threading.Thread(target=client.send_msg).start()
    
    
   