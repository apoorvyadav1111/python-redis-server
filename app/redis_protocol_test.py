from redis_protocol import RedisProtocol

def main():
    protocol = RedisProtocol()
    test_data = [
        "*1\r\n$4\r\nPING\r\n",
        ":1",
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
    if cnt == len(test_data):
        print("All tests passed!")
    else:
        print(f"{cnt}/{len(test_data)} tests passed.")


if __name__ == "__main__":
    main()