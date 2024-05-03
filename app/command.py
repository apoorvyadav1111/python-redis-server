class Command:
    @staticmethod
    def echo(data):
        return f"+{data}\r\n"

    @staticmethod
    def get(redis_store, key):
        value = redis_store.get(key):
        if value is None:
            return b"$-1\r\n"
        return value

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
        return b"+OK\r\n"

    @staticmethod
    def ping():
        return b"+PONG\r\n"


