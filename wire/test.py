import unittest
import io
import sys
import time
import client, server
from constants import *


server = server.Server("", 26222)
user_input = client.UserInput()
client = client.Client("localhost", 26222)

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
        self.assertEqual(print_it(user_input.do_login, ""), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input.do_login, "asdf"), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input.do_login, "username1password1  "), "Incorrect arguments: correct form is login [username] [password]. Please try again!")
        self.assertEqual(print_it(user_input.do_login, "username.special   password"), "Special characters not allowed in usernames. Please try again!")
        self.assertEqual(print_it(user_input.do_login, "u" * (MAX_LENGTH + 1) + " password"), "Username or password is too long. Please try again!")


    def test_login_privilege_error(self):
        pass

    def test_successful_login(self):
        pass

if __name__ == '__main__':
    unittest.main()