import unittest
import io
import sys
import time
import client, server
import threading
import inspect
import os
from constants import *


test_port = 26222
server = server.Server("", test_port, logs=False)
client1 = client.Client("localhost", test_port)
client2 = client.Client("localhost", test_port)
user_input1 = client.UserInput(client1)
user_input2 = client.UserInput(client2)

# redirect standard output of function f applied to arguments arg to string output
def print_it(f, arg):
      capturedOutput = io.StringIO() 
      sys.stdout = capturedOutput
      f(arg)
      time.sleep(1)
      sys.stdout = sys.__stdout__ 
      return capturedOutput.getvalue().strip()


# Each of these tests is run in the order listed here
class TestWireProtocol(unittest.TestCase):
    def test_register_client_errors(self):
        self.assertEqual(print_it(user_input1.do_register, ""), "Incorrect arguments: correct form is register [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_register, "asdf"), "Incorrect arguments: correct form is register [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_register, "username1password1  "), "Incorrect arguments: correct form is register [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_register, "username.special   password"), "Special characters not allowed in usernames. Please try again!")
        self.assertEqual(print_it(user_input1.do_register, "u" * (MAX_LENGTH + 1) + " password"), "Username or password is too long. Please try again!")

    def test_register_server_errors(self):
        self.assertEqual(print_it(user_input1.do_register, "user1 password1"), "user1 successfully registered, please log in!")
        self.assertEqual(server.users["user1"], "password1")
        self.assertEqual(print_it(user_input1.do_register, "user1 password456"), "Username already exists. Please try again!")
        self.assertEqual(server.users["user1"], "password1")

    def test_successful_register(self):
        self.assertEqual(print_it(user_input2.do_register, "3user password3"), "3user successfully registered, please log in!")
        self.assertEqual(print_it(user_input2.do_register, "asdf asdf"), "asdf successfully registered, please log in!")
        self.assertEqual(print_it(user_input2.do_register, "lawrence lawrence"), "lawrence successfully registered, please log in!")
        self.assertEqual(print_it(user_input2.do_register, "catherine catherine"), "catherine successfully registered, please log in!")

    def test_delete_logout_send_privilege_errors(self):
        self.assertEqual(print_it(user_input1.do_delete, ""), "You need to be logged in. Please try again!")
        self.assertEqual(print_it(user_input1.do_logout, ""), "You need to be logged in. Please try again!")
        self.assertEqual(server.users["user1"], "password1")
        self.assertEqual(print_it(user_input1.do_send, "user1 hi"), "You need to be logged in to send a message. Please try again!")

    def test_login_client_errors(self):
        self.assertEqual(print_it(user_input1.do_login, ""), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "asdf"), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "username1password1  "), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "username.special   password"), "Special characters not allowed in usernames. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "u" * (MAX_LENGTH + 1) + " password"), "Username or password is too long. Please try again!")

    def test_login_server_errors(self):
        self.assertEqual(print_it(user_input1.do_login, "user1 password2"), "Incorrect username or password. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "user234 password234"), "Incorrect username or password. Please try again!")
        self.assertEqual(server.active_conns, {})

    def test_login_success(self):
        self.assertEqual(print_it(user_input1.do_register, "user2 password2"), "user2 successfully registered, please log in!")
        self.assertEqual(server.users["user2"], "password2")
        self.assertEqual(print_it(user_input1.do_login, "user1 password1"), "Logged in as user1!")
        self.assertEqual(len(server.active_conns), 1)
        self.assertEqual(print_it(user_input2.do_login, "user2 password2"), "Logged in as user2!")
        self.assertEqual(len(server.active_conns), 2)

    def test_login_register_privilege_errors(self):
        self.assertEqual(print_it(user_input1.do_register, "user3 password3"), "You need to be logged out to register. Please try again!")
        self.assertEqual(print_it(user_input2.do_login, "user3 password3"), "You need to be logged out to login. Please try again!")

    def test_send_client_errors(self):
        self.assertEqual(print_it(user_input1.do_send, ""), "Incorrect arguments: correct form is send [username] [message]. Please try again!")
        self.assertEqual(print_it(user_input1.do_send, "user2"), "Incorrect arguments: correct form is send [username] [message]. Please try again!")
        self.assertEqual(print_it(user_input2.do_send, "user1 " + "m" * (MAX_LENGTH + 1)), "Username or message is too long. Please try again!")

    def test_send_server_errors(self):
        self.assertCountEqual(server.users.keys(), ["user1", "user2", "3user", "asdf", "lawrence", "catherine"])
        self.assertEqual(print_it(user_input1.do_send, "nonexistentuser hi"), "Recipient user does not exist. Please try again!")
        self.assertEqual(print_it(user_input2.do_send, "nonexistentuser hi"), "Recipient user does not exist. Please try again!")

    def test_successful_send(self):
        self.assertEqual(print_it(user_input1.do_send, "user2 hi"), "user1: hi")
        self.assertEqual(print_it(user_input1.do_send, "user1 hi2"), "user1: hi2")
        self.assertEqual(print_it(user_input2.do_send, "user2 hi3"), "user2: hi3")
        self.assertEqual(print_it(user_input2.do_send, "user1 hi4"), "user2: hi4")

    def test_find(self):
        self.assertCountEqual(server.users.keys(), ["user1", "user2", "3user", "asdf", "lawrence", "catherine"])
        self.assertEqual(print_it(user_input1.do_find, "."), "Users: user1, 3user, asdf, lawrence, catherine, user2")
        self.assertEqual(print_it(user_input1.do_find, "user"), "Users: user1, user2")
        self.assertEqual(print_it(user_input1.do_find, "3"), "Users: 3user")
        self.assertEqual(print_it(user_input1.do_find, "l.wr"), "Users: lawrence")
        self.assertEqual(print_it(user_input1.do_find, ".at"), "Users: catherine")

# function to identify what is a test class object in this file / module
def isTestClass(x):
    return inspect.isclass(x) and issubclass(x, unittest.TestCase)
# function to identify what is a test function in this file / module
def isTestFunction(x):
    return inspect.isfunction(x) and x.__name__.startswith("test")

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
    threading.Thread(target=server.run).start()
    threading.Thread(target=client1.send).start()
    threading.Thread(target=client1.receive).start()
    threading.Thread(target=client2.send).start()
    threading.Thread(target=client2.receive).start()
    # Ensures each of these tests is run in the order listed in the file
    runner = unittest.TextTestRunner()
    runner.run(suite())
    os._exit(1)

