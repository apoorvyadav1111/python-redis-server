# Uncomment this to pass the first stage
import socket
import asyncio
from app.resp.redis_protocol import RedisProtocol
from app.key_value_store import RedisStore
from app.command import Command
import sys
import argparse

KEY_VALUE_STORE = RedisStore()

server_meta = {
    "role": "master",
    "replica_host": None,
    "replica_port": None
}

async def handle_client(client_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    global lock
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
            async with lock:
                response = Command.set(KEY_VALUE_STORE, data[1:])
            await loop.sock_sendall(client_socket, response.encode())
        elif command == "GET":
            async with lock:
                response = Command.get(KEY_VALUE_STORE, data[1])
            await loop.sock_sendall(client_socket, response.encode())
        elif command == "INFO":
            response = Command.info(data[1:], server_meta)
            await loop.sock_sendall(client_socket, response.encode())




async def listen_forever(server_socket: socket.socket, loop: asyncio.AbstractEventLoop):
    while True:
        client_socket, addr = await loop.sock_accept(server_socket)
        client_socket.setblocking(False)
        loop.create_task(handle_client(client_socket, loop))

async def main(port: int):
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", port), reuse_port=True)
    server_socket.setblocking(False)
    loop = asyncio.get_event_loop()
    await listen_forever(server_socket, loop)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="Port number to listen on", type=int)
    parser.add_argument("--replicaof", help="Replicate data to another server", type=str, nargs=2)
    args = parser.parse_args()
    port = 6379
    try:
        if args.port:
            port = int(args.port)
    except ValueError:
        print("Invalid port")
        sys.exit(1)
    if args.replicaof:
        server_meta["role"] = "slave"
        server_meta["replica_host"] = args.replicaof[0]
        server_meta["replica_port"] = args.replicaof[1]
    print(f"Starting server on port {port}")
    print(f"Role: {server_meta['role']}"
          f"Replica Host: {server_meta['replica_host']}"
          f"Replica Port: {server_meta['replica_port']}")

    lock = asyncio.Lock()
    asyncio.run(main(port=port))
