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
            self.handle_message(message)
            
    def handle_message(self, message: Message):
        """Checks the title of the message and takes the appropriate action
        
        - RQMV (ReQuest MoVe): Peer is requesting to move to a new pos.
        - FNMV (Finish MoVe): Peer is signaling that has finished moving for the round
        - SCAN (SCAN peers): Peer is requesting which peers are withing its radio range
       
        """
        title = message.get_title()
        peer_name = message.get_name()
        self.log(f"Received {title} message from {peer_name}")
        round = message.get_round()
        destination = message.get_source_address()
        content = message.get_content()

        if round > self.round:
            self.log_important(f"{peer_name} IS AHEAD IN TIME CYCLES")
        
        if title == "RQMV":
            current_pos_str, new_pos_str = content.split("|")
            current_pos = utils.string_to_tuple(current_pos_str)
            new_pos = utils.string_to_tuple(new_pos_str)
            valid_move = self.change_pos(peer_name, current_pos, new_pos)
            if valid_move:
                accept_move_message = self.create_message("OKMV")
                self.connect(peer_name, accept_move_message, destination)
                self.moved_peers.append(peer_name)
            else:
                deny_move_message = self.create_message("DNMV")
                self.connect(peer_name, deny_move_message, destination)
        elif title == "FNMV":
            self.moved_peers.append(peer_name)
        elif title == "SCAN":
            peer_pos_str, radio_range_str = content.split("|")
            peer_pos = utils.string_to_tuple(peer_pos_str)
            radio_range = int(radio_range_str)

            peers_in_vicinity = self.find_peers(peer_pos, radio_range)
            peers_in_vicinity_message = self.create_message("PWIR", peers_in_vicinity)
            self.connect(peer_name, peers_in_vicinity_message, destination)
    
    def find_peers(self, peer_pos: tuple[str, int], radio_range: int):
        """Finds the peers that are withing range of the requesting peer"""
        peers_in_vicinity: list[tuple[str, tuple[str, int]]] = []
        x_cardinals = [peer_pos[0]]
        y_cardinals = [peer_pos[1]]

        for r in range(1, radio_range + 1):
            right = peer_pos[0] + r
            if right in range(self.SIZE):
                x_cardinals.append(right)
            
            left = peer_pos[0] - r
            if left in range(self.SIZE):
                x_cardinals.append(left)
            
            down = peer_pos[1] + r
            if down in range(self.SIZE):
                y_cardinals.append(down)
            
            up = peer_pos[1] - r
            if up in range(self.SIZE):
                y_cardinals.append(up)

        for x in x_cardinals:
            for y in y_cardinals:
                if self.area[x][y] != "#" and not (x == peer_pos[0] and y == peer_pos[1]):
                    with self.lock:
                        peer_name = self.area[x][y]
                    
                    self.log(f"Found {peer_name} at {x},{y}")

                    peer_address = self.peers_addresses[peer_name]
                    peers_in_vicinity.append((peer_name, peer_address))

        return peers_in_vicinity

    def change_pos(
            self,
            peer_name: str,
            current_pos: tuple[int, int],
            new_pos: tuple[int, int],
            ):
        """Checks to see if the move is legal. 

        If the move is legal, it updates the area and returns True.
        Otherwise it returns False

        """
        self.log(f"{peer_name} wants to change their position to {new_pos} ")
        valid_move = False
        x, y = new_pos
        if x in range(0, self.SIZE) and y in range(0, self.SIZE):
            with self.lock:
                if self.area[x][y] == "#":
                    valid_move = True

        if valid_move:
            with self.lock:
                #remove the current_pos 
                self.area[current_pos[0]][current_pos[1]] = "#"
                # note the new pos
                self.area[x][y] = peer_name
            
            return True
        
        return False

    def start_new_round(self, ):
        """Checks if a new round must start. If it is, it broadcasts a PASR message"""
        while True:
            if (len(self.moved_peers)) == self.MAX_PEERS:
                self.round += 1
                self.log_important("New Time Cycle")
                message = self.create_message("PASR")
                # send the broadcast message
                self.broadcast(message)
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
        # self.log(f"Opened connection with {peer_name}")
        threading.Thread(target=self.send, args=(peer_name, client_socket, message, )).start()

    def send(self, peer_name, client_socket: socket.socket, message: Message):
        encoded_message = message.encode()
        client_socket.send(encoded_message)
        self.log(f"Send {message.get_title()} message to {peer_name}")

        client_socket.close()
        self.log(f"Closed connection with {peer_name}")

    def bootstrap(self, peers: list["Peer"]):
        """Updates the peers positions, addresses and starts a broadcast"""
        for peer in peers:

            peer_name = peer.get_name()
            peer_address = peer.get_source_address()
            self.update_peers_addresses(peer_name, peer_address)

            peer_pos = peer.get_pos()
            self.area[peer_pos[0]][peer_pos[1]] = peer_name

        message = self.create_message("PASR")
        self.broadcast(message)


if __name__ == "__main__":
    server = Server(65432, 3, 2, 5)
    server.peers_addresses = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5
    }

    server.area = [
        ["A", "#", "E"],
        ["#", "B", "#"],
        ["C", "D", "E"]
    ]

    print(server.find_peers((0, 0), 2))