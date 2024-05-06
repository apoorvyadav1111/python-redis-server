# Uncomment this to pass the first stage
import socket
import asyncio
from app.resp.redis_protocol import RedisProtocol
from app.key_value_store import RedisStore
from app.command import Command
import sys
import argparse
from random import choices
from string import ascii_letters, digits
import base64

KEY_VALUE_STORE = RedisStore()

server_meta = {
    "role": "master",
    "replica_host": None,
    "replica_port": None,
    "master_repl_offset": 0,
    "master_replid": "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
}

async def send_handshake(master_host, master_port):
    handshake_1 = Command.send_ping().encode()
    reader, writer = await asyncio.open_connection(master_host, master_port)
    try:
        writer.write(handshake_1)
        await writer.drain()
        data = await reader.read(1024)
        response = RedisProtocol().parse(data.decode())
        if response != "PONG":
            raise Exception("Handshake step 1 failed")
        handshake_2_1 = Command.send_replconf("listening-port", "6380").encode()
        writer.write(handshake_2_1)
        await writer.drain()
        data = await reader.read(1024)
        response = RedisProtocol().parse(data.decode())
        if response != "OK":
            raise Exception("Handshake step 2 failed")
        handshake_2_2 = Command.send_replconf("capa", "pysnc2").encode()
        writer.write(handshake_2_2)
        await writer.drain()
        data = await reader.read(1024)
        response = RedisProtocol().parse(data.decode())
        if response != "OK":
            raise Exception("Handshake step 3 failed")
        handshake_3 = Command.send_psync("?", "-1").encode()
        writer.write(handshake_3)
        await writer.drain()
    finally:
        writer.close()

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
            response = Command.respond_to_ping()
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
        elif command == "REPLCONF":
            response = Command.respond_to_replconf()
            await loop.sock_sendall(client_socket, response.encode())
        elif command == "PSYNC":
            response = Command.respond_to_psync(server_meta["master_replid"], server_meta["master_repl_offset"])
            await loop.sock_sendall(client_socket, response.encode())
            with open("empty.rdb", "rb") as f:
                rdb_data = base64.b64encode(f.read())
                await loop.sock_sendall(client_socket, RedisProtocol().encode(rdb_data).encode())






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
    if server_meta["role"] == "master":
        server_meta["master_repl_offset"] = 0
        server_meta["master_replid"] = ''.join(choices(ascii_letters + digits, k=40))
    else:
        asyncio.run(send_handshake(server_meta["replica_host"], int(server_meta["replica_port"])))
    lock = asyncio.Lock()
    asyncio.run(main(port=port))
