from time import time

class Value:
    def __init__(self, value: str, px: int|None):
        self.value = value
        self.px = px

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

class RedisStore:
    def __init__(self):
        self.store = {}
    
    def set(self, key: str, value: str, px: int | None = None):
        if px is not None:
            self.store[key] = Value(value, time()+px/1000)
        else:
            self.store[key] = Value(value)
    
    def get(self, key: str):
        if key in self.store:
            value = self.store[key]
            if value.px is not None and time() > value.px:
                del self.store[key]
                return None
            return value.value
        return None