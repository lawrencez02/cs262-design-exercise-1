# Installation and Setup Instructions
Python version 3.7+ is required: the latest version of Python can be installed at [this link](https://www.python.org/downloads/).
For the wire protocol version, no additional Python libraries need to be installed. For the gRPC version, the Python library for gRPC needs to be installed at [this link](https://grpc.io/docs/languages/python/quickstart/).
Then, to run the server, navigate to the appropriate folder (either grpc or wire) and run "python server.py" or "python current_server.py". To start up a client, navigate to the appropriate folder and run "python client.py [HOST] [PORT]" for the wire version, where HOST is the server machine's address and PORT is the appropriate port number (currently hard-coded to 12984), or "python current_client.py [HOST] [PORT]" for the gRPC version. 
If you have trouble starting up the client or the server, be sure to disable your machine's firewall.

# How to Use
For both the wire and gRPC version, the client behavior is the same. There are 6 available application-related commands for the client to use: register, login, logout, delete, send, and find. 
register [username] [password] allows users to create an account. register must be run from a non-logged in client.
login [username] [password] allows users to login once they have an account. login must be run from a non-logged in client.
logout takes no arguments, and allows users to logout and subsequently also exits the chatbot. logout must be run from a logged-in client.
delete takes no arguments, and allows users to delete their account and subsequently exit the chatbot. delete must be run from a logged-in client.
send [username] [message] allows users to send a message to a specified user. send must be run from a logged-in client.
find [regex] allows users to find users on the chatbot by a regex expression.

Therefore, a typical workflow in the chat application might look like: "register User1 Password1", "login User1 Password1", some "send" or "find" commands, and finally a "logout" or "delete."

Note also that to close the chatbot clients or the server, you can press Control-C. Finally, you can also type "help" or "?" into the client command line to receive further help or clarification on any of the above commands. 

# Engineering Notebook
To see more technical discussion on the design of our wire protocol and the gRPC version, please see the following [engineering notebook](https://docs.google.com/document/d/1_woX4jMeICmyr4oACuNrLt2HmFSQO7RKk35GuqDuTLs/edit?usp=sharing).
