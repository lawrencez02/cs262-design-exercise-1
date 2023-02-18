from concurrent import futures 

import grpc 
import current_pb2
import current_pb2_grpc 
import queue
import time

messages_dict = {}
users = set()

class ChatBot(current_pb2_grpc.ChatBotServicer): 
    def login(self, request, context): 
        self.username = request.username 
        users.add(self.username)
        if self.username not in messages_dict: 
            messages_dict[self.username] = queue.Queue()
        return current_pb2.Empty()

    def send(self, request_iterator, context): 
        for request in request_iterator: 
            print("Got request " + str(request))
            if request.to_ not in messages_dict: 
                messages_dict[request.to_] = queue.Queue() 
            messages_dict[request.to_].put(request)    
    
    def receive(self, request, context): 
        while True: 
            request = messages_dict[self.username].get()
            message = current_pb2.Message(message=request.message, from_=request.from_, to_=request.to_)
            yield message
        
def server(): 
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    current_pb2_grpc.add_ChatBotServicer_to_server(ChatBot(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC starting")
    server.start()
    server.wait_for_termination()
server()