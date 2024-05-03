# Uncomment this to pass the first stage
import socket
import selectors
import types

PING = "*1\r\n$4\r\nPING\r\n"

def accept_connection(sock):
    conn, addr = sock.accept() # accept the connection
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    if mask and selectors.EVENT_READ:
        recv_data = sock.recv(1024).decode()
        if recv_data == PING:
            data.outb = b"+PONG\r\n"
        else:
            print("closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
    if mask and selectors.EVENT_WRITE:
        if data.outb:
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

    
def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    sel = selectors.DefaultSelector()
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.listen()
    server_socket.setBlocking(False)
    sel.register(server_socket, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_connection(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == "__main__":
    main()
