from concurrent import futures 
import grpc 
import current_pb2
import current_pb2_grpc 
import queue
import time
import os
import re

# users stores usernames as keys and corresponding passwords as values
users = {}
# messages_dict stores usernames as keys and thread-safe queue.Queue objects as values 
# messages_dict[username] stores all messages SENT TO username
# note that both users and messages_dict keep track of all accounts in the chatbot (active or otherwise)
messages_dict = {}

class ChatBot(current_pb2_grpc.ChatBotServicer): 

    def register(self, request, context): 
        # if the username provided is already in users, notify client 
        if request.username in users: 
            return current_pb2.Status(code=-1, message="Username already exists. Please try again!")
        # if username/password contains banned character (. * or spaces), notify client 
        elif bool(re.search(r'[\s.\*]', request.username)) or bool(re.search(r'\s', request.password)): 
            return current_pb2.Status(code=-1, message="Characters '.' and '*' not allowed in usernames. Spaces are not allowed in username or password. Please try again!")
        # otherwise, create an account with the specified username and password by adding username to users with corresponding password as value and adding username to messages_dict with corresponding empty queue.Queue() object as value 
        else: 
            users[request.username] = request.password 
            messages_dict[request.username] = queue.Queue()
            return current_pb2.Status(code=1, message="You've successfully registered. Please login to start sending messages.")
    
    def login(self, request, context): 
        # if username can't be found in users or password doesn't match, tell client to try again 
        if request.username not in users or users[request.username] != request.password: 
            return current_pb2.Status(code=-1, message="Incorrect username or password. Please try again!")
        # otherwise, notify client they've successfully logged in 
        else: 
            return current_pb2.Status(code=1, message=f"Logged in as {request.username}!")    

    def delete(self, request, context): 
        if request.username in users and request.username in messages_dict:
            del users[request.username]
            del messages_dict[request.username]
            return current_pb2.Status(code=1, message=f"{request.username} deleted successfully!")
        else: 
            return current_pb2.Status(code=-1, message="You need to be logged in. Please try again!")

    def send(self, request, context): 
        print("Got request " + str(request))
        if request.from_ not in users:
            return current_pb2.Status(code=-1, message="You need to be logged in to send a message. Please try again!") 
        if request.to_ in messages_dict: 
            messages_dict[request.to_].put(request)
            return current_pb2.Status(code=1, message="")
        else: 
            return current_pb2.Status(code=-1, message="Recipient user does not exist. Please try again!")

    def receive(self, request, context): 
        username = request.username
        while True: 
            request = messages_dict[username].get()
            if not context.is_active(): 
                messages_dict[username].put(request)
                break
            message = current_pb2.Message(message=request.message, from_=request.from_, to_=request.to_)
            yield message
    
    def find(self, request, context): 
        exp = request.username 
        regex = re.compile(exp)
        result = list(filter(regex.match, users.keys()))
        for res in result: 
            username = current_pb2.Username(username=res)
            yield username

        
def server(): 
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    current_pb2_grpc.add_ChatBotServicer_to_server(ChatBot(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC starting")
    server.start()
    try: 
        server.wait_for_termination()
        while True: time.sleep(100)
    except KeyboardInterrupt: 
        print("Caught keyboard interruption exception, server exiting.")
    finally: 
        os._exit(1)

if __name__ == '__main__':
    server()
    