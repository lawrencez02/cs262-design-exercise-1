import grpc 
from cmd import Cmd
import current_pb2
import current_pb2_grpc
import queue
import threading
import time

write_queue = queue.Queue() 

class UserInput(Cmd): 
    def do_login(self, username): 
        self.client = Client(username)
        self.client.login()
        x = threading.Thread(target=self.client.send)
        y = threading.Thread(target=self.client.receive)
        x.start() 
        y.start()
        
    def do_send(self, info):
        to_, msg = info.split(" ", 1)
        write_queue.put((msg, self.client.username, to_))

class Client:
    def __init__(self, username): 
        self.username = username   
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = current_pb2_grpc.ChatBotStub(self.channel)
        self.stream = self.stub.receive(current_pb2.Empty())
        
    def login(self): 
        self.stub.login(current_pb2.User(username=self.username))

    def iterator(self): 
        while True:
            msg, from_, to_ = write_queue.get() 
            message = current_pb2.Message(message=msg, from_=from_, to_=to_)
            yield message 
    
    def send(self): 
        with grpc.insecure_channel('localhost:50051') as channel: 
            stub = current_pb2_grpc.ChatBotStub(channel) 
            stub.send(self.iterator())
            
    def receive(self): 
        while True: 
            message = next(self.stream)
            print(message.from_, ": ", message.message)
                
if __name__ == '__main__':
    z = threading.Thread(target=UserInput().cmdloop)
    z.start()

