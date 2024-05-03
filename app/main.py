# Uncomment this to pass the first stage
import socket
import asyncio
from app.resp.redis_protocol import RedisProtocol
from app.key_value_store import RedisStore
from app.command import Command

KEY_VALUE_STORE = RedisStore()

async def handle_client(client_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    redis_protocol = RedisProtocol()
    while data := await loop.sock_recv(client_socket, 1024):
        data = redis_protocol.parse(data.decode())
        if not isinstance(data, list):
            await loop.sock_sendall(client_socket, b"-ERR\r\n")
            continue
        command = data[0].upper()
        if command == "PING":
            response = Command.ping()
            await loop.sock_sendall(client_socket, response.encode())
        elif command == "ECHO":
            response = Command.echo(data[1:])
            await loop.sock_sendall(client_socket, response.encode())
        elif command == "SET":
            response = Command.set(KEY_VALUE_STORE, data[1:])
            await loop.sock_sendall(client_socket, response.encode())
        elif "GET" in data:
            response = Command.get(KEY_VALUE_STORE, data[1])
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
