# Installation and Setup Instructions
Python version 3.7+ is required: the latest version of Python can be installed at [this link](https://www.python.org/downloads/).
For the wire protocol version, no additional Python libraries need to be installed. For the gRPC version, the Python library for gRPC needs to be installed at [this link](https://grpc.io/docs/languages/python/quickstart/).
Then, to run the server, navigate to the appropriate folder (either grpc or wire) and run "python server.py" or "python current_server.py". To start up a client, navigate to the appropriate folder and run "python client.py [HOST] [PORT]" for the wire version, where HOST is the server machine's address and PORT is the appropriate port number (currently hard-coded to 12984), or "python current_client.py [HOST] [PORT]" for the gRPC version. 
If you have trouble starting up the client or the server, be sure to disable your machine's firewall.

# How to Use
For both the wire and gRPC version, the client behavior is the same. There are 6 available application-related commands for the client to use: register, login, logout, delete, send, and find. 
* register [username] [password] allows users to create an account. register must be run from a non-logged in client. Note that register does not automatically login after the account is successfully registered. To login, users must separately submit a login command. 
    * Register will have a confirmation message if it was successfully completed, and it will have an error message if not (e.g., for incorrect command syntax, usernames and/or passwords too long or usernames having certain special characters, username already existing, or for current client already being logged in).
* login [username] [password] allows users to login once they have an account. login must be run from a non-logged in client.
    * Login will have a confirmation message if it was successfully completed, and it will have an error message if not (e.g., for incorrect command syntax, usernames and/or passwords too long, usernames having certain special characters, incorrect username or password, desired account already logged in elsewhere, or for current client already being logged in).  
* logout ignores any arguments given, and allows the currently logged-in user to logout and subsequently also exits the chatbot. logout must be run from a logged-in client.
    * Logout will have a confirmation message if it was successfully completed, also shutting down the client program completely, and it will have an error message if not (e.g., for user not being logged in currently).
* delete ignores any arguments given, and allows the currently logged-in user to delete that account and subsequently exit the chatbot. delete must be run from a logged-in client.
    * Delete will have a confirmation message if it was successfully completed, also shutting down the client program completely, and it will have an error message if not (e.g., for user not being logged in currently).
* send [username] [message] allows users to send a message to a specified user. send must be run from a logged-in client.
    * Send will have no confirmation message if it was successfully completed, and it will have an error message if not (e.g., incorrect syntax, message or username too long, current client not being logged in, or recipient username not existing as an account).
* find [regex] allows users to find users on the chatbot by a regex expression.
    * Find will return the result of the user search if it was successfully completed, and it will have an error message otherwise (e.g., incorrect syntax or regex expression too long).
    * For specific details on how Python regex works, please see [this documentation](https://www.w3schools.com/python/python_regex.asp). The most important thing to note is that "." is a wildcard character. Note that our regex matches a username if any substring of the username matches the regex expression (e.g., "." will thus match any username). 

Therefore, a typical workflow in the chat application might look like: "register User1 Password1", "login User1 Password1", some "send" or "find" commands, and finally a "logout" or "delete." There is a limit on username/password/message size, but it is large and probably will not be encountered in everyday use. 

Note that to close the chatbot clients or the server, you can press Control-C. Finally, you can also type "help" or "?" into the client command line to receive further help or clarification on any of the above commands. Note also that the command-line input will give an error message stating a command is of unknown syntax if it does not belong to one of the above forms (matching lowercase and all).

# Testing
Note that in our testing we focus only on the logic and functionality of our client code, server code, and the wire protocol in-between. In particular, we do NOT test the functionality of various libraries that we used, such as the Cmd library, and instead take those by assumption to be fully functional. We created unit tests using the Python unittest framework, in test.py files.

# Engineering Notebook
For more documentation and details on the chatbot functions, and to see more technical discussion on the design of our wire protocol and the gRPC version, please see the following [engineering notebook](https://docs.google.com/document/d/1_woX4jMeICmyr4oACuNrLt2HmFSQO7RKk35GuqDuTLs/edit?usp=sharing).
