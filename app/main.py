# Uncomment this to pass the first stage
import socket
import asyncio

PING = "*1\r\n$4\r\nPING\r\n"
PONG = "+PONG\r\n"

async def handle_client(client_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    while data := await loop.sock_recv(client_socket, 1024):
        if data.encode() == PING:
            await loop.sock_sendall(client_socket, PONG.decode())



async def listen_forever(server_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    while True:
        client_socket, addr = await loop.sock_accept(server_socket)
        client_socket.setblocking(False)
        await loop.create_task(handle_client(client_socket, loop))

async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.setblocking(False)
    loop = asyncio.get_event_loop()
    await listen_forever(server_socket, loop)

if __name__ == "__main__":
    asyncio.run(main())
