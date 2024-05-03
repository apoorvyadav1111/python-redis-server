# Uncomment this to pass the first stage
import socket
import asyncio
from app.resp.redis_protocol import RedisProtocol

PING = "*1\r\n$4\r\nPING\r\n"
PONG = "+PONG\r\n"

class RedisProtocol:
    def __init__(self):
        self.idx = 0
        self.tokens = []
        self.__symbols_to_types = {
            '*': 'array',
            '+': 'simple_string',
            '$': 'bulk_string',
            ':': 'integer',
            '-': 'error',
            '_': 'null',
            '#': 'boolean',
            ',': 'double',
            '(': 'big_number',
            '!': 'bulk_error',
            '=': 'verbatim_string',
            '%': 'map',
            '~': 'set',
            '>': 'pushes'
        }
        self.__types_to_symbols = {
            'array': '*',
            'simple_string': '+',
            'bulk_string': '$',
            'integer': ':',
            'error': '-',
            'null': '_',
            'boolean': '#',
            'double': ',',
            'big_number': '(',
            'bulk_error': '!',
            'verbatim_string': '=',
            'map': '%',
            'set': '~',
            'pushes': '>'
        }
    
    def tokenize(self,data):
        if data == '':
            return []
        tokens = data.split('\r\n')
        if len(tokens) == 0:
            return []
        return tokens
    
    def parse(self,tokens):
        self.idx = 0
        self.tokens = self.tokenize(tokens)
        if len(tokens) == 0:
            return []
        else:
            return self.decode()

    def __get_type(self, token):
        return self.__symbols_to_types[token[0]]
    
    def __types_to_symbols(self, type):
        return self.__types_to_symbols[type]

    def decode(self):
        kind = self.__get_type(self.tokens[self.idx])
        if kind == 'array':
            return self.__decode_array()
        elif kind == 'simple_string':
            return self.__decode_simple_string()
        elif kind == 'bulk_string':
            return self.__decode_bulk_string()
        elif kind == 'integer':
            return self.__decode_integer()
        elif kind == 'error':
            return self.__decode_error()
        elif kind == 'null':
            return None
        elif kind == 'boolean':
            return self.__decode_boolean()
        else:
            return None
    
    def __decode_array(self):
        length = int(self.tokens[self.idx][1:])
        self.idx += 1
        i = 0
        result = []
        while i<length:
            value = self.decode()
            result.append(value)
            i += 1
        return result
    
    def __decode_simple_string(self):
        value = self.tokens[self.idx][1:]
        self.idx += 1
        return value
    
    def __decode_bulk_string(self):
        length = int(self.tokens[self.idx][1:])
        self.idx += 1
        value = self.tokens[self.idx]
        self.idx += 1
        return value

    def __decode_integer(self):
        value = int(self.tokens[self.idx][1:])
        self.idx += 1
        return value
    
    def __decode_boolean(self):
        value = self.tokens[self.idx][1:]
        self.idx += 1
        return value == 't'

    def encode(self,data):
        pass
async def handle_client(client_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    redis_protocol = RedisProtocol()
    while data := await loop.sock_recv(client_socket, 1024):
        data = redis_protocol.parse(data.decode())
        if data == ["PING"]:
            await loop.sock_sendall(client_socket, PONG.encode())
        elif "ECHO" in data:
            response = f"+{data[1]}\r\n"
            await loop.sock_sendall(client_socket, response.encode())



async def listen_forever(server_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    while True:
        client_socket, addr = await loop.sock_accept(server_socket)
        client_socket.setblocking(False)
        loop.create_task(handle_client(client_socket, loop))

async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.setblocking(False)
    loop = asyncio.get_event_loop()
    await listen_forever(server_socket, loop)

if __name__ == "__main__":
    asyncio.run(main())
