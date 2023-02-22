import unittest
import io
import sys
import time
import client, server
import threading
from constants import *


test_port = 2622
server1 = server.Server("", test_port, logs=False)
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

    def test_login_privilege_error(self):
        self.assertEqual(print_it(user_input1.do_register, "user1 password1"), "user1 successfully registered, please log in!")
        self.assertEqual(server.users["user1"], "password1")

    def test_successful_login(self):
        pass

if __name__ == '__main__':
    threading.Thread(target=server1.run).start()
    threading.Thread(target=client1.send).start()
    threading.Thread(target=client1.receive).start()
    threading.Thread(target=client2.send).start()
    threading.Thread(target=client2.receive).start()
    unittest.main()

