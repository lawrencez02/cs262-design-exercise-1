import unittest 
import current_pb2_grpc 
import grpc 
import current_server
from concurrent import futures 
import current_client
import queue
import io
import sys
import os
import time
import inspect
from unittest import mock 
import signal

# run a server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=40))
current_pb2_grpc.add_ChatBotServicer_to_server(current_server.ChatBot(), server)
server.add_insecure_port('[::]:11111')
server.start()

# create two clients, client1 and client2
client1 = current_client.Client('localhost', 11111) 
user_input1 = current_client.UserInput(client1)

client2 = current_client.Client('localhost', 11111) 
user_input2 = current_client.UserInput(client2)

# function to identify what is a test class object in this file / module
def isTestClass(x):
    return inspect.isclass(x) and issubclass(x, unittest.TestCase)
# function to identify what is a test function in this file / module
def isTestFunction(x):
    return inspect.isfunction(x) and x.__name__.startswith("test")

def print_it(f,arg):
      capturedOutput = io.StringIO() 
      sys.stdout = capturedOutput
      f(arg)
      time.sleep(0.2)
      sys.stdout = sys.__stdout__ 
      return capturedOutput.getvalue().strip()

class TestRegister(unittest.TestCase):
    def test_register_successful(self): 
        self.assertEqual(print_it(user_input1.do_register, "username1 password"),"username1 successfully registered, please log in!")
        self.assertEqual(current_server.users["username1"], "password")
        self.assertEqual(type(current_server.messages_dict["username1"]), queue.Queue)
        self.assertTrue(current_server.messages_dict["username1"].empty())
    
    def test_register_client_errors(self): 
        def test_register_with_already_existing_username(self): 
            self.assertEqual(print_it(user_input2.do_register, "username1 password"),"Username already exists. Please try again!")
        def test_register_with_special_characters(self): 
            self.assertEqual(print_it(user_input2.do_register, "* password"),"Special characters not allowed in usernames. Please try again!")
        def test_register_with_incorrect_arguments(self):
            self.assertEqual(print_it(user_input2.do_register, "register"), "Incorrect arguments: correct form is register [username] [password]. Please try again!")
        
class TestLogin(unittest.TestCase): 
    def test_login_client_errors(self): 
        self.assertEqual(print_it(user_input1.do_login, "username1"), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, ""), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "username1 passWORD"), "Incorrect username or password. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "username2 password2"), "Incorrect username or password. Please try again!")

    def test_login_successful(self): 
        self.assertEqual(print_it(user_input1.do_login, "username1 password"), "Logged in as username1!")

class TestLoginAndRegister(unittest.TestCase): 
    def test_register_after_logged_in(self): 
        self.assertEqual(print_it(user_input1.do_register, "blah blah"), "You need to be logged out. Please try again!")

    def test_login_after_logged_in(self): 
        self.assertEqual(print_it(user_input1.do_login, "blah blah"), "You need to be logged out. Please try again!")
    
class TestSend(unittest.TestCase): 
    def test_send_messages_to_yourself(self): 
        self.assertEqual(print_it(user_input1.do_send, "username1 hi"), "username1: hi")

    def test_send_client_errors(self): 
        self.assertEqual(print_it(user_input2.do_send, "username1 hi"), "You need to be logged in to send a message. Please try again!")
        self.assertEqual(print_it(user_input1.do_send, "username2 hi"), "Recipient user does not exist. Please try again!")
        self.assertEqual(print_it(user_input1.do_send, ""),"Incorrect arguments: correct form is send [username] [message]. Please try again!")
        self.assertEqual(print_it(user_input1.do_send, "username"),"Incorrect arguments: correct form is send [username] [message]. Please try again!")

    def test_send_messages_to_logged_out_client(self): 
        user_input2.do_register("username2 password")
        user_input1.do_send("username2 welcome to the chatbot")
        user_input1.do_send("username2 I'm really glad you're here!")
        self.assertEqual(print_it(user_input2.do_login, "username2 password"), "Logged in as username2!\nusername1: welcome to the chatbot\nusername1: I'm really glad you're here!")

    def test_send_messages_between_two_logged_in_clients(self): 
        self.assertEqual(print_it(user_input2.do_send, "username1 I'm really glad to be here :)"), "username2: I'm really glad to be here :)")
        self.assertEqual(print_it(user_input1.do_send, "username2 I'm glad to hear it."), "username1: I'm glad to hear it.") 
    
class TestFind(unittest.TestCase): 
    def test_find(self): 
        self.assertEqual(print_it(user_input1.do_find, "usern"), "username1\nusername2")
        self.assertEqual(print_it(user_input1.do_find, "username1"), "username1")
        self.assertEqual(print_it(user_input1.do_find, ""), "username1\nusername2")
        self.assertEqual(print_it(user_input1.do_find, "."), "username1\nusername2")
        self.assertEqual(print_it(user_input1.do_find, "u."), "username1\nusername2")

class TestLogout(unittest.TestCase): 
    def test_logout(self): 
        client4 = current_client.Client('localhost', 11111) 
        user_input4 = current_client.UserInput(client4)
        user_input4.do_register("username4 password4")
        user_input4.do_login("username4 password4")
        os._exit = unittest.mock.MagicMock()
        user_input4.do_delete("")
        assert os._exit.called

class TestDelete(unittest.TestCase): 
    def setUp(self): 
        def f(x):
            if x == 2: 
                return
            else: 
                sys.exit()
        os._exit = f
    def test_delete_client_error(self): 
        client3 = current_client.Client('localhost', 11111) 
        user_input3 = current_client.UserInput(client3)
        user_input3.do_register("username3 password3")
        self.assertEqual(print_it(user_input3.do_delete, ""), "You need to be logged in. Please try again!")

    def test_delete_successful(self): 
        self.assertEqual(print_it(user_input1.do_delete, ""), "username1 deleted successfully!")
        self.assertFalse("username1" in current_server.users)
        self.assertFalse("username1" in current_server.messages_dict)
        self.assertEqual(print_it(user_input2.do_send, "username1 hi"), "Recipient user does not exist. Please try again!")


def suite(): 
    # get current module 
    module = sys.modules[__name__]
    # get a list of (class names, class object) tuples for all the classes defined above (in current module)
    testClasses = [tup for tup in inspect.getmembers(module, isTestClass)]
    # sort the classes by line number
    testClasses.sort(key=lambda t: inspect.getsourcelines(t[1])[1])

    testSuite = unittest.TestSuite()

    # for each class
    for testClass in testClasses:
        # get list of (testFunctionName,testFunction) tuples in that class
        classTests = [
            tup for tup in
            inspect.getmembers(testClass[1], isTestFunction)
        ]
        # sort by line number
        classTests.sort(key=lambda t: inspect.getsourcelines(t[1])[1])
        # for each class, create TestCase instances
        # add to testSuite;
        for test in classTests:
            testSuite.addTest(testClass[1](test[0]))

    return testSuite

if __name__ == '__main__': 
    runner = unittest.TextTestRunner()
    runner.run(suite())
    os._exit(3)
   