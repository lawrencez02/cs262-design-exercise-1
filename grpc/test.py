import current_pb2_grpc 
import grpc 
import current_server
from concurrent import futures 
import current_client
import queue
import io
import sys
import os
import difflib
import time

# we want to capture what is printed to the terminal 
def print_it(f,arg):
      # create StringIO object
      capturedOutput = io.StringIO() 
      # redirect sys.stdout to capturedOutput
      sys.stdout = capturedOutput
      f(arg)
      time.sleep(1)
      sys.stdout = sys.__stdout__ 
      return capturedOutput.getvalue().strip()

# create a server which is listening on a testing port 11111
server = grpc.server(futures.ThreadPoolExecutor(max_workers=40))
current_pb2_grpc.add_ChatBotServicer_to_server(current_server.ChatBot(), server)
server.add_insecure_port('[::]:11111')
server.start()

# create a client on a testing host / port (localhost, 11111)
client1 = current_client.Client('localhost', 11111) 
# create a commandline interface object for client1
user_input1 = current_client.UserInput(client1)

# logging in before registering 
assert(print_it(user_input1.do_login, "username1 password") == "Incorrect username or password. Please try again!")
# registering with valid username and password 
assert(print_it(user_input1.do_register, "username1 password") == "You've successfully registered. Please login to start sending messages.")
assert(current_server.users["username1"] == "password")
assert(type(current_server.messages_dict["username1"]) == queue.Queue)
assert(current_server.messages_dict["username1"].empty())
# registering with invalid username and password 
assert(print_it(user_input1.do_register, '. .') == "Characters '.' and '*' not allowed in usernames. Spaces are not allowed in username or password. Please try again!")

# logging in after registering with correct username and password
assert(print_it(user_input1.do_login, "username1 password") == "Logged in as username1!")
# check to make sure a logged in user cannot log in again 
assert(print_it(user_input1.do_login, "username1 password") == "You need to be logged out. Please try again!")
# check to make sure a logged in user can send a message to themselves and receive it on the command line 
assert(print_it(user_input1.do_send, "username1 hi") == "username1 : hi")

# creating another client using same process as before
client2 = current_client.Client('localhost', 11111) 
user_input2 = current_client.UserInput(client2)

assert(print_it(user_input2.do_register, "username2 password") == "You've successfully registered. Please login to start sending messages.")
# check to make sure that sending to a user who isn't logged in exhibits desired behavior (i.e. once the user logs in, they see all the messages sent to them while they weren't logged in)
user_input1.do_send("username2 welcome to the chatbot")
user_input1.do_send("username2 I'm really glad you're here!")
assert(print_it(user_input2.do_login, "username2 password") == "Logged in as username2!\nusername1 : welcome to the chatbot\nusername1 : I'm really glad you're here!")
# test to make sure sending a message to a user who is logged in works properly (i.e. message delivers immediately)
assert(print_it(user_input2.do_send, "username1 I'm really glad to be here :)") == "username2 : I'm really glad to be here :)")
# test to make sure that if user tries to use do_send improperly, a descriptive error message shows up
assert(print_it(user_input1.do_send, "send") == "Incorrect arguments: correct form is send [username] [message]. Please try again!")
# test to make sure sending a message to a user who is logged in works properly (i.e. message delivers immediately)
assert(print_it(user_input1.do_send, "username2 I'm glad to hear it.") == "username1 : I'm glad to hear it.") 
# test find function 
assert(print_it(user_input1.do_find, "usern") == "username1\nusername2")
# print(print_it(user_input1.do_find, "*"))
assert(print_it(user_input1.do_find, "username1") == "username1")




# testing (1) deleting an account, (2) logging out, and (3) sending messages after loggnig out then logging back in is complicated by the fact that logout uses os._exit(1)
# therefore, we manually these three things - please read more about it in the Testing section of our engineering notebook 

