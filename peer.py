import socket
import threading
from message import Message
class Peer:
    def __init__(self, name: str, pos: tuple[int, int], server_port: int):
        self.name = name
        self.pos = pos
        self.SOURCE_ADDRESS = ("127.0.0.1", server_port)
        self.cycle = 0

    def serve(self):
        serve_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serve_socket.bind(self.SOURCE_ADDRESS)
        serve_socket.listen(5)
        
        while True:
            peer_socket, peer_address = serve_socket.accept()
            threading.Thread(target=self.handle_peer, args=(peer_socket, peer_address, )).start()
    
    def handle_peer(self, peer_socket, peer_address):
        threading.Thread(target=self.receive, args=(peer_socket, ))

    def receive(self, peer_socket):
        while True:
            data = peer_socket.recv(1024)
            if data:
                message: Message = Message.decode(data)
                self.handle_message(peer_socket, message)

    def handle_message(self, peer_socket, message):
        pass

if __name__ == "__main__":
    peer =  Peer("Alice", (0, 0), 65444)
    # peer.serve()
    # peer.move()
