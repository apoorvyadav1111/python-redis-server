# Uncomment this to pass the first stage
import socket

PING = "*1\r\n$4\r\nping\r\n"
def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    while True:
        conn, addr = server_socket.accept() # accept the connection
        while True:
            data = conn.recv(1024).decode()
            if data == PING:
                conn.sendall("+PONG\r\n".encode())
        conn.close()


if __name__ == "__main__":
    main()
