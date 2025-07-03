import socket
import threading

class Server:
    def __init__(self, host: str, port: int, size: int):
        """Initialize a server that tracks the positions of peers"""
        self.server_address = (host, port)
        self.move_peers = []
        self.SIZE = size
        self.area = [[0 for _ in range(size)] for _ in range(size)]


    def listen(self) -> socket.socket:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(self.server_address)
        server_socket.listen(1)
        print(f"Listening at {self.server_address}")
        return server_socket

    def serve(self, server_socket):
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connected to {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket, )).start()


    def handle_client(self, client_socket):
        send_thread = threading.Thread(target=self.send, args=(client_socket, b"Hello back"))
        recv_thread = threading.Thread(target=self.receive, args=(client_socket, ))
        recv_thread.start()
        send_thread.start()
            

    def send(self, client_socket, message):
        #for sending bigger messages
        client_socket.send(message)
        print("Send data")

    def receive(self, client_socket: socket.socket):
        while True:
            data = client_socket.recv(1024)
            if data:
                self.handle_message(data)
            

    def connect(self, peer_address):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(peer_address)
        message = f"Hello from {self.server_address}"
        send_thread = threading.Thread(target=self.send, args=(client_socket, message.encode(), ))
        recv_thread = threading.Thread(target=self.receive, args=(client_socket, ))
        recv_thread.start()
        send_thread.start()

        recv_thread.join()
        send_thread.join()
        client_socket.close()
        print("Connection ended")


def handle_server(server: Server, address):
    t = 0
    while t < 10:
        server_socket = server.listen()
        threading.Thread(target=server.serve, args=(server_socket, )).start()

        connect_thread = threading.Thread(target=server.connect, args=(address, ))
        connect_thread.start()




if __name__ == "__main__":
    pass




# handle_peer = recv and then handle the type of messages
# holds a queue and parses it with receive so that it can sends its pass time messages