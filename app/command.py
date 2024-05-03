class Command:
    @staticmethod
    def echo(data):
        l = 0
        echo_data = ""
        for i in range(len(data)):
            echo_data += f"{data[i]}\r\n"
            l += len(data[i])
        return f"${l}\r\n{echo_data}"

    @staticmethod
    def get(redis_store, key):
        value = redis_store.get(key)
        if value is None:
            return "$-1\r\n"
        return f"${len(value)}\r\n{value}\r\n"

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
        return "+OK\r\n"

    @staticmethod
    def ping():
        return "+PONG\r\n"


