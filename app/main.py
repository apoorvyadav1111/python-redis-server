# Uncomment this to pass the first stage
import socket

PING = "*1\r\n$4\r\nping\r\n"
def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    conn, addr = server_socket.accept() # accept the connection
    conn.sendall("+PONG\r\n".encode()) # send the response


if __name__ == "__main__":
    main()
