import grpc 
from cmd import Cmd
import current_pb2
import current_pb2_grpc
import queue
import threading
import time
import sys 

write_queue = queue.Queue() 
channel = grpc.insecure_channel('localhost:50051')
stub = current_pb2_grpc.ChatBotStub(channel)
logged_in = False

"""
try:
    grpc.channel_ready_future(channel).result(timeout=1)
except:
    print("Server not ready")
    sys.exit()
"""

class UserInput(Cmd): 

    def do_register(self, register_info): 
        try: 
            username, password = register_info.split(" ")
        except: 
            print("Make sure you specify a username and a password.")
            return 
        status = stub.register(current_pb2.User(username=username, password=password))
        print(status.err)

    def do_login(self, login_info): 
        try: 
            username, password = login_info.split(" ")
        except: 
            print("Make sure you specify a username and a password.")
            return 
        status = stub.login(current_pb2.User(username=username, password=password))
        if status.status == 1: 
            self.client = Client(username)
            global logged_in
            logged_in = True 
            y = threading.Thread(target=self.client.receive)
            y.start()
        else: 
            print(status.err)
        
    def do_send(self, info):
        if not logged_in: 
            print("You aren't logged in yet.")
        else: 
            try: 
                to_, msg = info.split(" ", 1)
            except: 
                print("Make sure you specify a recipient and a message.")
                return 
            status = stub.send(current_pb2.Message(message=msg, from_=self.client.username, to_=to_))
            if status.status == -1: 
                print(status.err)
    
    def do_logout(self, none): 
        global logged_in 
        logged_in = False 
        channel.close() 
        sys.exit()

class Client:
    def __init__(self, username): 
        self.username = username
        self.receive_stream = stub.receive(current_pb2.User(username=self.username, password=""))
            
    def receive(self): 
        while True: 
            try:
                message = next(self.receive_stream)
                print(message.from_, ": ", message.message)
            except: 
                break
                
if __name__ == '__main__':
    z = threading.Thread(target=UserInput().cmdloop)
    z.start()

