import socket
import threading
import log
import utils
from message import Message

class Server:
    """Represents a central server that helps with position and connectivity betwween peers
    
    Attributes:

        name (str): the name of the server (just for logging purposes)
        logger (Logger): logs all the actions of the peer
        server_ADDRESS (tuple[str, int]): address the server actively listens to
        peers_addresses (dict[str: tuple[str, int]]): a dictionary with all the
        addresses
        moved_peers (list[str]): tracks which peers have taken their move action
        round (int): the round the server is in
        END_ROUND (int): the round after which logging is disabled
        MAX_PEERS: the number of peers in the simulation
        SIZE: the area's side size
        area: a rectangle area where peers can move to
        lock: locks the are when a peer changes its pos
        """
    def __init__(self, port: int, size: int, max_peers: int, END_ROUND: int):
        self.name = "Server"
        self.logger = log.create_logger()
        self.SERVER_ADDRESS = ("127.0.0.1", port)
        self.peers_addresses: dict[str: tuple[str, int]] = {}
        self.moved_peers: list[str] = []
        self.round: int = 1
        self.END_ROUND: int = END_ROUND
        self.MAX_PEERS: int = max_peers
        self.SIZE: int = size
        self.area: list[list[str]] = [["#" for _ in range(size)] for _ in range(size)]
        self.lock: threading.Lock = threading.Lock()

    def get_peer_address(self, peer_name: str) -> str:
        """Returns the peer's address"""
        return self.peers_addresses[peer_name]
    
    def update_peers_addresses(self, peer_name: str, peer_address: tuple[str, int]):
        """Adds a new peer to the peers_addresses"""
        self.peers_addresses[peer_name] = peer_address

    def log(self, message):
        """Logs a server's message up until END_ROUND"""
        if self.round < self.END_ROUND:
            self.logger.info(message, extra={"peer_name": self.name, "round": self.round})

    def log_important(self, message):
        """Logs a server's important message up until END_ROUND"""
        if self.round < self.END_ROUND:
            self.logger.info(f"\x1b[31m{message}\x1b[0m", extra={"peer_name": self.name, "round": self.round})

    def serve(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(self.SERVER_ADDRESS)
        server_socket.listen(5)
        
        while True:
            client_socket, client_address = server_socket.accept()
            # self.log(f"Opened connection with {client_address}")
            threading.Thread(target=self.receive, args=(client_socket, client_address)).start()

    def create_message(self, title: str, content=""):
        message = Message(
            title=title,
            round=self.round,
            name=self.name,
            source_address=self.SERVER_ADDRESS,
            content=content
        )

        return message

    def receive(self, client_socket: socket.socket, client_address: str):
        while True:
            data = client_socket.recv(1024)
            if not(data):
                client_socket.close()
                # self.log(f"Closed address with {client_address}")
                break

            message = Message.decode(data)
            threading.Thread(target=self.handle_message, args=(message, )).start()
            
    def handle_message(self, message: Message):
        """Checks the title of the message and takes the appropriate action
        
        - RQMV (ReQuest MoVe): Peer is requesting to move to a new pos.
        - FNMV (Finish MoVe): Peer is signaling that has finished moving for the round
       
        """
        title = message.get_title()
        peer_name = message.get_name()
        self.log(f"Received {title} message from {peer_name}")
        round = message.get_round()
        destination = message.get_source_address()

        if round > self.round:
            self.log_important(f"{peer_name} IS AHEAD IN TIME CYCLES")
        
        if title == "RQMV":
            current_pos_str, new_pos_str = message.get_content().split("|")
            current_pos = utils.string_to_tuple(current_pos_str)
            new_pos = utils.string_to_tuple(new_pos_str)
            threading.Thread(target=self.change_pos, args=(peer_name, current_pos, new_pos, destination, )).start()
        elif title == "FNMV":
            self.store(peer_name)

    def change_pos(
            self,
            peer_name: str,
            current_pos: tuple[int, int],
            new_pos: tuple[int, int],
            destination: tuple[str, int]
            ):
        """Checks to see if the move is legal and send the appropriate message
        
        If the move is legal, also store the peer's name to moved_peers

        """
        self.log(f"{peer_name} wants to change their position to {new_pos} ")
        x, y = new_pos
        with self.lock:
            if  x not in range(0, self.SIZE) or \
                y not in range(0, self.SIZE) or \
                self.area[x][y] != "#":

                message = self.create_message("DNMV")
                threading.Thread(target=self.connect, args=(peer_name, message, destination, )).start()
            else:
                #remove the current_pos
                self.area[current_pos[0]][current_pos[1]] = "#"
                # note the new pos
                self.area[x][y] = peer_name
                message = self.create_message("OKMV")
                accepted_move_thread: threading.Thread = threading.Thread(target=self.connect, args=(peer_name, message, destination, ))
                accepted_move_thread.start()
                # Want the `OKMV` message to first reach the target and then start a new
                # round if able
                accepted_move_thread.join()
                self.log(f"Send OKMV message to {peer_name}")
                self.store(peer_name)

    def store(self, peer_name: str):
        """Stores the name of peer to the moved_peer list
        
        If the list reaches its maximum, begin a new cycle
        
        """
        self.moved_peers.append(peer_name)

        if (len(self.moved_peers)) == self.MAX_PEERS:
            self.round += 1
            self.log_important("New Time Cycle")
            message = self.create_message("PASR")
            # send the broadcast message
            broadcast_thread = threading.Thread(target=self.broadcast, args=(message, ))
            broadcast_thread.start()
            broadcast_thread.join()
            # after the broadcast, clear the list of moved peers
            self.moved_peers.clear()
            
    def broadcast(self, message: Message):
        """Broadcasts a message to all peers"""
        self.log("Sending broadcast")
        for peer_name, address in self.peers_addresses.items():
            threading.Thread(target=self.connect, args=(peer_name, message, address, )).start()
        
    def connect(self, peer_name: str, message: Message, destination: tuple[str, int]):
        """Connects with a specific peer and deliver it a message"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect(destination)
        self.log(f"Opened connection with {peer_name}")
        threading.Thread(target=self.send, args=(peer_name, client_socket, message, )).start()

    def send(self, peer_name, client_socket: socket.socket, message: Message):
        encoded_message = message.encode()
        client_socket.send(encoded_message)
        self.log(f"Send {message.get_title()} message to {peer_name}")

        client_socket.close()
        self.log(f"Closed connection with {peer_name}")

    def start(self, peers: list["Peer"]):
        """Updates the peers_addresses with all the peers and starts a broadcast"""
        for peer in peers:
            peer_name = peer.get_name()
            peer_address = peer.get_source_address()
            self.update_peers_addresses(peer_name, peer_address)
        message = self.create_message("PASR")
        self.broadcast(message)


if __name__ == "__main__":
    server = Server("127.0.0.1", 65432, 4, 3)
    server.handle_message(Message("RQMV", 0, "Olivia", "safd", "[1, 2]|[3, 4]"))