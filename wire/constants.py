# General constants
PORT = 12984
MAX_LENGTH = 2 ** 10 # max argument length (e.g., username, password, message, etc.)


# OP CODES (what client sends to server)
LOGIN = 0
REGISTER = 2
LOGOUT = 4
SEND = 8
FIND = 16

# STATUS/RESPONSE CODES (what server sends to client)
LOGIN_CONFIRM = LOGIN
LOGIN_ERROR = 1
REGISTER_CONFIRM = REGISTER
REGISTER_ERROR = 3
LOGOUT_CONFIRM = LOGOUT
RECEIVE = SEND
SEND_ERROR = 9
FIND_RESULT = FIND
PRIVILEGE_ERROR = 64
