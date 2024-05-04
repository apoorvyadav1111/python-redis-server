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
    def ping():
        return RedisProtocol().encode(Response("PONG", 'simple_string'))
    
    @staticmethod
    def info(data):
        response = ""
        for i in range(0, len(data)):
            if data[i].upper() == "REPLICATION":
                response += "# Replication\r\nrole:master\r\n"
                return RedisProtocol().encode(Response(response, 'bulk_string'))
    


