# General constants
PORT = 12984
MAX_LENGTH = 2 ** 10 # max argument length in wire protocol (e.g., username, password, message, etc.)


# OP CODES (what client sends to server)
LOGIN = 0
REGISTER = 4
LOGOUT = 8
DELETE = 12
SEND = 16
FIND = 20

# STATUS/RESPONSE CODES (what server sends to client)
LOGIN_CONFIRM = LOGIN
LOGIN_ERROR = LOGIN + 1
REGISTER_CONFIRM = REGISTER
REGISTER_ERROR = REGISTER + 1
LOGOUT_CONFIRM = LOGOUT
DELETE_CONFIRM = DELETE
RECEIVE = SEND
SEND_ERROR = SEND + 1
FIND_RESULT = FIND
PRIVILEGE_ERROR = 64
