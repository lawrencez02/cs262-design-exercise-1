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
        elif any(c in ".+*?^$()[]{}|\\" for c in request.username): 
            return current_pb2.Status(code=-1, message="Special characters not allowed in usernames. Please try again!")
        # otherwise, create an account with the specified username and password by adding username to users with corresponding password as value and adding username to messages_dict with corresponding empty queue.Queue() object as value 
        else: 
            users[request.username] = request.password 
            messages_dict[request.username] = queue.Queue()
            return current_pb2.Status(code=1, message=f"{request.username} successfully registered, please log in!")
    
    def login(self, request, context): 
        # if username can't be found in users or password doesn't match, tell client to try again 
        if request.username not in users or users[request.username] != request.password: 
            return current_pb2.Status(code=-1, message="Incorrect username or password. Please try again!")
        # otherwise, notify client they've successfully logged in 
        else: 
            return current_pb2.Status(code=1, message=f"Logged in as {request.username}!")    

    def delete(self, request, context): 
        # only make it possible to delete account if the account exists in users and messages_dict 
        # if it does, remove that username and its associated values from both users and message_dict
        if request.username in users and request.username in messages_dict:
            del users[request.username]
            del messages_dict[request.username]
            return current_pb2.Status(code=1, message=f"{request.username} deleted successfully!")
        else: 
            return current_pb2.Status(code=-1, message="You need to be logged in. Please try again!")

    def send(self, request, context): 
        # check to make sure request.from_ is a valid username
        if request.from_ not in users:
            return current_pb2.Status(code=-1, message="You need to be logged in to send a message. Please try again!") 
        # check to make sure request.to_ is a valid user
        # if yes, put the message in messages_dict[request.to_]
        if request.to_ in messages_dict: 
            messages_dict[request.to_].put(request)
            return current_pb2.Status(code=1, message="")
        # if request.to_ isn't a valid user, send appropriate Status 
        else: 
            return current_pb2.Status(code=-1, message="Recipient user does not exist. Please try again!")

    def receive(self, request, context): 
        username = request.username
        # to receive messages, use a while True loop to constantly get messages from messages_dict[username] 
        while True: 
            # take a message from messages_dict[username] if possible
            request = messages_dict[username].get()
            # this line of code makes sure the channel is still active 
            # if the channel is no longer active, put the message you just got from messages_dict[username] queue back and break out of the while True loop
            if not context.is_active(): 
                messages_dict[username].put(request)
                break
            # package the message into a Message object
            message = current_pb2.Message(message=request.message, from_=request.from_, to_=request.to_)
            # yield back to client (yield is how to return a stream in gRPC)
            yield message
    
    def find(self, request, context): 
        # when the user calls find, it packages the expression they're looking for into a Username object: Username(username=expression)
        # get the expression the user is looking for
        exp = request.username 
        # match using re module and return as a stream 
        regex = re.compile(exp)
        result = list(filter(regex.match, users.keys()))
        for res in result: 
            username = current_pb2.Username(username=res)
            yield username

        
def server(): 
    # create a server object
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=40))
    # add_ChatBotServicer_to_server is a function automatically generated in current_pb2_grpc and links server-side implementation to server object created above
    current_pb2_grpc.add_ChatBotServicer_to_server(ChatBot(), server)
    # specify which port server is listening to
    server.add_insecure_port('[::]:12984')
    print("gRPC starting")
    # start the server 
    server.start()
    try: 
        # block current thread until server stops
        server.wait_for_termination()
        # sleep to make sure main loop doesn't exit before catching 
        while True: time.sleep(100)
    # handle keyboard exceptions
    except KeyboardInterrupt: 
        print("Caught keyboard interruption exception, server exiting.")
    finally: 
        os._exit(1)

# main loop 
if __name__ == '__main__':
    server()
    