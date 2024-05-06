from app.resp.redis_protocol import RedisProtocol, Response
class Command:
    @staticmethod
    def echo(data):
        resp = Response(data[0], 'bulk_string')
        return RedisProtocol().encode(resp)

    @staticmethod
    def get(redis_store, key):
        value = redis_store.get(key)
        if value is None:
            return RedisProtocol().encode(Response(None, 'null_bulk_string'))
        return RedisProtocol().encode(Response(value, 'bulk_string'))

    @staticmethod
    def set(redis_store, data):
        value = {
            "key": data[0],
            "value": data[1],
            "px": None
        }
        for i in range(2, len(data)):
            if data[i].upper() == "PX":
                value["px"] = int(data[i + 1])
        redis_store.set(value["key"], value["value"], value["px"])
        return RedisProtocol().encode(Response("OK", 'simple_string'))
    
    @staticmethod
    def send_ping():
        return RedisProtocol().encode(Response([Response("PING", "bulk_string")],"array"))
    
    @staticmethod
    def respond_to_ping():
        return RedisProtocol().encode(Response("PONG", 'simple_string'))
    
    @staticmethod
    def send_replconf(key, value):
        resp = Response([Response("REPLCONF", "bulk_string"), Response(key, "bulk_string"), Response(value, "bulk_string")], "array")
        return RedisProtocol().encode(resp)
    
    @staticmethod
    def respond_to_replconf():
        return RedisProtocol().encode(Response("OK", 'simple_string'))

    @staticmethod
    def info(data, server_meta):
        response = ""
        for i in range(0, len(data)):
            if data[i].upper() == "REPLICATION":
                response += f"# Replication\r\nrole:{server_meta["role"]}\r\n"
                response += f"master_replid:{server_meta["master_replid"]}\r\n"
                response += f"master_repl_offset:{server_meta["master_repl_offset"]}\r\n"
                print(RedisProtocol().encode(Response(response, 'bulk_string')))
                return RedisProtocol().encode(Response(response, 'bulk_string'))
    
    @staticmethod
    def send_psync(repl_id, offset):
        resp = Response([Response("PSYNC", "bulk_string"), Response(repl_id, "bulk_string"), Response(offset, "bulk_string")], "array")
        return RedisProtocol().encode(resp)

    @staticmethod
    def respond_to_psync(repl_id, offset):
        string = f"FULLRESYNC {repl_id} {offset}\r\n"
        return RedisProtocol().encode(Response(string, 'simple_string'))
    
    @staticmethod
    def send_rdb():
        return RedisProtocol().encode(Response("H", 'rdb_file'))
