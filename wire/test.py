import unittest
import io
import sys
import time
import client, server
import threading
import inspect
import os
from constants import *


test_port = 2622
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


class TestLogin(unittest.TestCase):
    def test_login_client_errors(self):
        self.assertEqual(print_it(user_input1.do_login, ""), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "asdf"), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "username1password1  "), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "username.special   password"), "Special characters not allowed in usernames. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "u" * (MAX_LENGTH + 1) + " password"), "Username or password is too long. Please try again!")

    def test_login_server_errors(self):
        self.assertEqual(print_it(user_input1.do_register, "user1 password1"), "user1 successfully registered, please log in!")
        self.assertEqual(server.users["user1"], "password1")
        self.assertEqual(server.active_conns, {})
        self.assertEqual(print_it(user_input1.do_login, "user1 password2"), "Incorrect username or password. Please try again!")
        self.assertEqual(print_it(user_input1.do_login, "user234 password234"), "Incorrect username or password. Please try again!")

    def test_login_server_errors_2_and_success(self):
        self.assertEqual(print_it(user_input1.do_register, "user2 password2"), "user2 successfully registered, please log in!")
        self.assertEqual(server.users["user2"], "password2")
        self.assertEqual(print_it(user_input1.do_login, "user1 password1"), "Logged in as user1!")
        self.assertEqual(print_it(user_input2.do_login, "user2 password2"), "Logged in as user2!")

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
    runner = unittest.TextTestRunner()
    runner.run(suite())
    os._exit(1)

