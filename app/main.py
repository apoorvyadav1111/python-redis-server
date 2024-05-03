# Uncomment this to pass the first stage
import socket
import asyncio
from resp.redis_protocol import RedisProtocol

PING = "*1\r\n$4\r\nPING\r\n"
PONG = "+PONG\r\n"

async def handle_client(client_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    redis_protocol = RedisProtocol()
    while data := await loop.sock_recv(client_socket, 1024):
        data = redis_protocol.parse(data.decode())
        if data == ["PING"]:
            await loop.sock_sendall(client_socket, PONG.encode())
        else:
            response = "$3\r\nhey\r\n"
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
