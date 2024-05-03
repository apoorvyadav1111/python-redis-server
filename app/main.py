# Uncomment this to pass the first stage
import socket
import asyncio
from app.resp.redis_protocol import RedisProtocol

KEY_VALUE_STORE = {}

async def handle_client(client_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    redis_protocol = RedisProtocol()
    while data := await loop.sock_recv(client_socket, 1024):
        data = redis_protocol.parse(data.decode())
        if data == ["PING"]:
            response = "+PONG\r\n"
            await loop.sock_sendall(client_socket, response.encode())
        elif "ECHO" in data:
            response = f"+{data[1]}\r\n"
            await loop.sock_sendall(client_socket, response.encode())
        elif "SET" in data:
            KEY_VALUE_STORE[data[1]] = data[2]
            await loop.sock_sendall(client_socket, b"+OK\r\n")
        elif "GET" in data:
            if data[1] in KEY_VALUE_STORE:
                response = f"${len(KEY_VALUE_STORE[data[1]])}\r\n{KEY_VALUE_STORE[data[1]]}\r\n"
                await loop.sock_sendall(client_socket, response.encode())
            else:
                await loop.sock_sendall(client_socket, b"$-1\r\n")





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
