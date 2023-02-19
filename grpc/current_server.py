from concurrent import futures 
from threading import current_thread
import grpc 
import current_pb2
import current_pb2_grpc 
import queue
import time

users = {}
# every user has a messages_dict, regardless of whether or not they're logged in 
messages_dict = {}

class ChatBot(current_pb2_grpc.ChatBotServicer): 

    def register(self, request, context): 
        if request.username in messages_dict: 
            return current_pb2.Status(status=-1, err="Username taken.")
        elif ' ' in request.username or ' ' in request.password: 
            return current_pb2.Status(status=-1, err="Neither username nor password are allowed to have any spaces.")
        else: 
            users[request.username] = request.password 
            messages_dict[request.username] = queue.Queue()
            return current_pb2.Status(status=1, err="You've successfully registered. Please login to start sending messages.")
    
    def login(self, request, context): 
        if request.username not in users or users[request.username] != request.password: 
            return current_pb2.Status(status=-1, err="Wrong username or password")
        else: 
            return current_pb2.Status(status=1, err="You are logged in!")                

    def send(self, request, context): 
        print("Got request " + str(request))
        if request.to_ in messages_dict: 
            messages_dict[request.to_].put(request)
            return current_pb2.Status(status=1, err="")
        else: 
            return current_pb2.Status(status=-1, err="User doesn't exist.")

    def receive(self, request, context): 
        username = request.username
        while True: 
            request = messages_dict[username].get()
            if not context.is_active(): 
                messages_dict[username].put(request)
                break
            message = current_pb2.Message(message=request.message, from_=request.from_, to_=request.to_)
            yield message
        
def server(): 
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    current_pb2_grpc.add_ChatBotServicer_to_server(ChatBot(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC starting")
    server.start()
    server.wait_for_termination()
server()