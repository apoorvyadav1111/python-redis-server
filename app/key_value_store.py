from datetime import datetime

class Value:
    def __init__(self, value: str, px: int|None, created_at: int):
        self.value = value
        self.px = px
        self.created_at = created_at

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

class RedisStore:
    def __init__(self):
        self.store = {}
    
    def set(self, key: str, value: str, px: int | None = None):
        self.store[key] = Value(value, px, datetime.now().timestamp())
    
    def get(self, key: str):
        if key in self.store:
            value = self.store[key]
            if value.px is not None and datetime.now().timestamp() - value.created_at > value.px:
                del self.store[key]
                return None
            return value
        return None