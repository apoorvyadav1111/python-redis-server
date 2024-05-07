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
lock = asyncio.Lock()
server_meta = {
    "role": "master",
    "replica_host": None,
    "replica_port": None,
    "master_repl_offset": 0,
    "master_replid": "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb",
    "replicas" : {}
}

def isMaster():
    return server_meta["role"] == "master"

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
        data = await reader.read(1024)


    finally:
        writer.close()



async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global lock
    try:
        addr = writer.get_extra_info('peername')
        redis_protocol = RedisProtocol()
        while reader.at_eof() is False:
            raw_data = await reader.read(1024)
            data = redis_protocol.parse(raw_data.decode())
            if not isinstance(data, list):
                writer.write("-ERR\r\n".encode())
                await writer.drain()
                continue
            command = data[0].upper()
            if command == "PING":
                response = Command.respond_to_ping()
                writer.write(response.encode())
                await writer.drain()
            elif command == "ECHO":
                response = Command.echo(data[1:])
                writer.write(response.encode())
                await writer.drain()
            elif command == "SET":
                async with lock:
                    response = Command.set(KEY_VALUE_STORE, data[1:])
                    if isMaster():
                        writer.write(response.encode())
                        await writer.drain()
                        for replica_conn in server_meta["replicas"].values():
                            replica_conn.write(response.encode())
                            await replica_conn.drain()
            elif command == "GET":
                async with lock:
                    response = Command.get(KEY_VALUE_STORE, data[1])
                writer.write(response.encode())
                await writer.drain()
            elif command == "INFO":
                response = Command.info(data[1:], server_meta)
                writer.write(response.encode())
                await writer.drain()
            elif command == "REPLCONF":
                if data[1] == "listening-port":
                    if isMaster():
                        server_meta["replicas"][addr] = writer
                response = Command.respond_to_replconf()
                writer.write(response.encode())
                await writer.drain()
            elif command == "PSYNC":
                response = Command.respond_to_psync(server_meta["master_replid"], server_meta["master_repl_offset"])
                writer.write(response.encode())
                await writer.drain()
                with open("app/empty.rdb", "rb") as f:
                    rdb_data = base64.b64decode(f.read())
                    writer.write(rdb_data)
                    await writer.drain()
    except Exception as e:
        print(e)
    finally:
        writer.close()
        await writer.wait_closed()


async def start_server(port: int):
    server = await asyncio.start_server(handle_client, port=port)
    async with server:
        await server.serve_forever()

async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")
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
    coroutines = []
    server = asyncio.create_task(start_server(port=port))
    coroutines.append(server)
    if server_meta["role"] == "slave":
        coroutines.append(send_handshake(server_meta["replica_host"], server_meta["replica_port"]))
    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
