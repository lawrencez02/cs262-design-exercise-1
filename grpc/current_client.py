import grpc 
from cmd import Cmd
import current_pb2
import current_pb2_grpc
import threading
import time
import os
import sys

# Command line interface: constantly listens for and handles command line input from users
class UserInput(Cmd): 
    # users will see this intro as soon as python current_client.py is run 
    intro = 'Welcome! Type help or ? to list commands. To see what a particular command does and how to invoke it, type help <command>. \n'

    def __init__(self, client): 
        # give access to all methods and properties of the parent class (Cmd)
        super().__init__()
        # needs to know about client to access the stub (self.client.stub) 
        self.client = client

    def do_register(self, register_info): 
        # specifies what users will see when they type help register 
        "Description: This command allows users to create an account. \nSynopsis: register [username] [password] \n"
        # self.client.username is only set after logging in successfully 
        # therefore if self.client.username is set, user is already logged in and shouldn't be able to register
        if self.client.username: 
            print("You need to be logged out. Please try again!")
            return 
        # split command line arguments in username and password 
        register_info = register_info.split(' ')
        if len(register_info) != 2:
            print(f"Incorrect arguments: correct form is register [username] [password]. Please try again!")
            return
        username, password = register_info
        # package username and password into User and call stub.register 
        status = self.client.stub.register(current_pb2.User(username=username, password=password))
        print(status.message)
    
    def do_login(self, login_info): 
        # specifies what users will see when they type help login
        "Description: This command allows users to login once they have an account. \nSynopsis: login [username] [password] \n"
        # checks if user is logged in; if yes, shouldn't be allowed to login again
        if self.client.username: 
            print("You need to be logged out. Please try again!")
            return 
        # split command line arguments in username and password
        login_info = login_info.split(' ')
        if len(login_info) != 2:
            print("Incorrect arguments: correct form is login [username] [password]. Please try again!")
            return
        username, password = login_info 
        # package username and password into User and call stub.login
        status = self.client.stub.login(current_pb2.User(username=username, password=password))
        # if login was successful, set self.client.username and set self.client.receive_stream to be the stream of messages returned by self.client.stub.receive 
        if status.code == 1: 
            self.client.username = username
            self.client.receive_stream = self.client.stub.receive(current_pb2.Username(username=self.client.username))
            # start the thread which iterates through self.client.receive_stream and prints them out
            y = threading.Thread(target=self.client.receive)
            y.start()
        print(status.message)

    def do_send(self, info):
        # specifies what users will see when they type help send
        "Description: This command allows users to send a message. \nSynopsis: send [username] [password] \n"
        # split command line arguments into send_to and message
        info = info.split(' ', 1)
        if len(info) != 2:
            print("Incorrect arguments: correct form is send [username] [message]. Please try again!")
            return
        to_, msg = info
        # package message, send_to, and your own username into a Message
        # call stub.send 
        status = self.client.stub.send(current_pb2.Message(message=msg, from_=self.client.username, to_=to_))
        # only print status message if there's an error
        if status.code == -1: 
            print(status.message)
    
    def do_logout(self, none): 
        # specifies what users will see when they type help logout
        "Description: This command allows users to logout and subsequently exit the chatbot. \nSynopsis: logout \n"
        # close channel 
        self.client.channel.close() 
        # shut down program 
        os._exit(1)

    def do_delete(self, none): 
        # specifies what users will see when they type help delete
        "Description: This command allows users to delete their account and subsequently exit the chatbot. \nSynopsis: delete\n"
        # package username into a Username and call stub.delete 
        status = self.client.stub.delete(current_pb2.Username(username=self.client.username))
        print(status.message)
        # close channel 
        self.client.channel.close() 
        # shut down program 
        os._exit(1)

    def do_find(self, exp): 
        # specifies what users will see when they type help find
        # exp is what the users type in (i.e. the username they want to find)
        # package exp into Username object, give to stub.find, and save return value of stub.find in results
        results = self.client.stub.find(current_pb2.Username(username=exp))
        # stub.find returns an iterator, so results should be iterated over
        for result in results: 
            print(result.username)


class Client:
    def __init__(self, host, port): 
        # no username until client is logged in 
        self.username = None
        # open channel at the specified host and port which server is listening on and create stub 
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = current_pb2_grpc.ChatBotStub(self.channel)
    
    # function which constantly iterates through the stream returned by stub.receive call for new messages and prints them 
    def receive(self): 
        while True: 
            try:
                message = next(self.receive_stream)
                print(message.from_, ":", message.message)
            # exception occurs when channel is closed and thus self.receive_stream  is cancelled (either because there's been some type of failure or someone has stopped the server)
            # in this case, shut down program 
            except grpc.RpcError: 
                print("Server shutting down.")
                os._exit(1)
                
if __name__ == '__main__':
    try: 
        # create an instance of Client class because the moment this file is run, we technically have a new client 
        host, port = sys.argv[1], int(sys.argv[2])
        client = Client(host, port)
        # start the thread which runs the command line interface and constantly listens for user input 
        z = threading.Thread(target=UserInput(client).cmdloop)
        z.start()
        # sleep to make sure main loop doesn't exit before catching the exception 
        while True: time.sleep(100)
    # if ctrl c is hit, shut down program 
    except KeyboardInterrupt: 
        print("Caught keyboard interrupt exception, client exiting")
        os._exit(1)
    # if any other exceptions are caught (for example, something wrong with server), also shut down program.
    except: 
        print("Exception caught, client existing.")
        os._exit(1)
