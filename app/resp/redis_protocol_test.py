from redis_protocol import RedisProtocol
from redis_protocol import Response
def main():
    protocol = RedisProtocol()
    test_data = [
        "*1\r\n$4\r\nPING\r\n",
        ":1\r\n",
        "*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n",
        "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n",
        "*2\r\n$4\r\necho\r\n$3\r\nhey\r\n",
        "*3\r\n$4\r\necho\r\n$3\r\nhey\r\n:1\r\n",
        "*3\r\n$4\r\necho\r\n$3\r\nhey\r\n*2\r\n$4\r\necho\r\n$3\r\nbye\r\n",
        "+PONG\r\n",
        "_\r\n",
        "#t\r\n",
        "#f\r\n"
    ]
    correct_results = [
        ["PING"],
        1,
        ["GET", "key"],
        ["SET", "key", "value"],
        ["echo", "hey"],
        ["echo", "hey", 1],
        ["echo", "hey", ["echo","bye"]],
        "PONG",
        None,
        True,
        False
    ]

    cnt = 0
    for data, correct_result in zip(test_data, correct_results):
        result = protocol.parse(data)
        if result == correct_result:
            print(f"Test passed: {result} == {correct_result}")
            cnt += 1
        else:
            print(f"Error: {result} != {correct_result}")
    print("RESP decode tests complete.")
    if cnt == len(test_data):
        print("All tests passed!")
    else:
        print(f"{cnt}/{len(test_data)} tests passed.")

    send_data = [
        Response([Response("PING", "bulk_string")], "array"),
        Response(1, "integer"),
        Response([Response("GET", "bulk_string"), Response("key", "bulk_string")], "array"),
        Response([Response("SET", "bulk_string"), Response("key", "bulk_string"), Response("value", "bulk_string")], "array"),
        Response([Response("echo", "bulk_string"), Response("hey", "bulk_string")], "array"),
        Response([Response("echo", "bulk_string"), Response("hey", "bulk_string"), Response(1, "integer")], "array"),
        Response([Response("echo", "bulk_string"), Response("hey", "bulk_string"), Response([Response("echo", "bulk_string"), Response("bye", "bulk_string")], "array")], "array"),
        Response("PONG", "simple_string"),
        Response(None, "null"),
        Response(True, "boolean"),
        Response(False, "boolean")
    ]

    cnt = 0
    for data, test_data in zip(send_data, test_data):
        result = protocol.encode(data)
        if result == test_data:
            cnt += 1
        else:
            print(f"Error: {result} != {test_data}")

    print("RESP encode tests complete.")
    if cnt == len(send_data):
        print("All tests passed!")
    else:
        print(f"{cnt}/{len(send_data)} tests passed.")

if __name__ == "__main__":
    main()