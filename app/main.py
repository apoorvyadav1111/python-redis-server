# Uncomment this to pass the first stage
import socket

PING = "*1\r\n$4\r\nping\r\n"
def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.accept() # wait for client
    conn, addr = socket_socket.accept() # accept the connection
    data = conn.recv(1024) # receive the data
    print(data)
    conn.sendall(b"+PONG\r\n") # send the response


if __name__ == "__main__":
    main()
