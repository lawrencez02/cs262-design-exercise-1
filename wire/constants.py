# General constants
PORT = 12984
MAX_LENGTH = 2 ** 10 # max argument length (e.g., username, password, message, etc.)


# OP CODES (what client sends to server)
LOGIN = 0
SEND = 8
FIND = 16
REGISTER = 24

# STATUS/RESPONSE CODES (what server sends to client)
LOGIN_CONFIRM = LOGIN
LOGIN_ERROR = 1
RECEIVE = SEND
SEND_ERROR = 9
FIND_RESULT = FIND
REGISTER_CONFIRM = REGISTER
REGISTER_ERROR = 25
PRIVILEGE_ERROR = 64
