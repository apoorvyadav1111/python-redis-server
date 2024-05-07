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
    "master_repl_offset": 0,
    "master_replid": "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb",
    "replicas" : {}
}

def isMaster():
    return server_meta["role"] == "master"

async def send_handshake(address, replica_port):
    handshake_1 = Command.send_ping().encode()
    host, port = address
    reader, writer = await asyncio.open_connection(host, port)
    try:
        writer.write(handshake_1)
        await writer.drain()
        data = await reader.read(1024)
        response = RedisProtocol().parse(data.decode())
        if response != "PONG":
            raise Exception("Handshake step 1 failed")
        handshake_2_1 = Command.send_replconf("listening-port",str(replica_port)).encode()
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

        redis_protocol = RedisProtocol()
        while reader.at_eof() is False:
            original_data = await reader.read(1)
            if original_data != b"*":
                writer.write("-ERR\r\n".encode())
                await writer.drain()
                continue
            num_of_args = await reader.readuntil(b"\r\n")
            original_data += num_of_args + b"\r\n"
            num_of_args = int(num_of_args.decode().strip())
            for i in range(num_of_args):
                data_kind = await reader.read(1)
                original_data += data_kind
                if data_kind == b"$":
                    data = await reader.readuntil(b"\r\n")
                    original_data += data + b"\r\n"
                    data = int(data.decode().strip())
                    read_data = await reader.read(data + 2)
                    original_data += read_data
            print(original_data)
            data = redis_protocol.parse(original_data.decode())
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
                print("HERE", server_meta["role"])
                async with lock:
                    response = Command.set(KEY_VALUE_STORE, data[1:])
                if isMaster():
                    writer.write(response.encode())
                    await writer.drain()
                    for replica_conn in server_meta["replicas"].values():
                        print("Sending to replica")
                        replica_conn.write(response.encode())
                        print("Sent to replica")
                        await replica_conn.drain()
                else:
                    print("In slave")
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
                        server_meta["replicas"][(addr,data[2])] = writer
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
    finally:
        writer.close()
        await writer.wait_closed()



async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global lock
    try:
        print("Connected", server_meta["role"])
        addr = writer.get_extra_info('peername')
        redis_protocol = RedisProtocol()
        while reader.at_eof() is False:
            original_data = await reader.read(1)
            if original_data != b"*":
                writer.write("-ERR\r\n".encode())
                await writer.drain()
                continue
            num_of_args = await reader.readuntil(b"\r\n")
            num_of_args = int(num_of_args.decode().strip())
            original_data += num_of_args + b"\r\n"
            for i in range(num_of_args):
                data_kind = await reader.read(1)
                original_data += data_kind
                if data_kind == b"$":
                    data = await reader.readuntil(b"\r\n")
                    original_data += data + b"\r\n"
                    data = int(data.decode().strip())
                    read_data = await reader.read(data + 2)
                    original_data += read_data

            data = redis_protocol.parse(original_data.decode())
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
                print("HERE", server_meta["role"])
                async with lock:
                    response = Command.set(KEY_VALUE_STORE, data[1:])
                if isMaster():
                    writer.write(response.encode())
                    await writer.drain()
                    for replica_conn in server_meta["replicas"].values():
                        print("Sending to replica")
                        replica_conn.write(response.encode())
                        print("Sent to replica")
                        await replica_conn.drain()
                else:
                    print("In slave")
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
                        server_meta["replicas"][(addr,data[2])] = writer
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
    server = asyncio.create_task(start_server(port=port))
    coroutines = [server]
    if args.replicaof:
        server_meta["role"] = "slave"
    if server_meta["role"] == "master":
        server_meta["master_repl_offset"] = 0
        server_meta["master_replid"] = ''.join(choices(ascii_letters + digits, k=40))
    if server_meta["role"] == "slave":
        handshake = asyncio.create_task(send_handshake(args.replicaof, args.port))
        coroutines.append(handshake)
    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
