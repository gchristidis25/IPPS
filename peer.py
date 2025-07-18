import socket
import threading
import log
from threadpool import Threadpool
from message import Message

class Peer:
    """Represents a mobile phone whose user moves randomly every round

    Attributes:
        logger (Logger): logs all the actions of the peer
        name (str): peer's name
        pos (tuple[int, int]): peer's position
        SOURCE_ADDRESS (tuple[str, int]): address the peers actively listens to
        round (int): the round the peer is in
        END_ROUND (int): the round after which logging is disabled
        DIRECTIONS (list[str]): the four possible cardinal direction the peer can move in
        random_directions (list[str]): the subsets of possible directions the peer
        chose to make in a given round
        next_pos (tuple[int, int]): the position the peer chose to move next
        RADIO_RANGE (int): the WiFi range
        peers_in_vicinity (list[str, tuple[int, str]]): the peers and their
        addresses that are withing radio range
        threadpool (Threadpool): the simulation's threadpool
        serving_module_active (bool): a flag that controls the serving operation
        of the peer
    
    """
    def __init__(
            self,
            name: str,
            pos: tuple[int, int],
            server_port: int,
            END_ROUND: int,
            server_address:tuple[str, int],
            radio_range: int,
            threadpool: Threadpool
            ):
        self.logger = log.create_logger()
        self.name: str = name
        self.pos: tuple[int, int] = pos
        self.SOURCE_ADDRESS: tuple[str, int] = ("127.0.0.1", server_port)
        self.SERVER_ADDRESS: tuple[str, int] = server_address
        self.round: int = 0
        self.END_ROUND: int = END_ROUND
        self.DIRECTIONS: list[str] = ["up", "down", "left", "right"]
        self.random_directions: list[str] = []
        self.next_pos: tuple[int, int] = None
        self.RADIO_RANGE: int = radio_range
        self.peers_in_vicinity = []
        self.threadpool = threadpool
        self.serving_module_active: bool = True

    def get_name(self):
        """Returns the peer's name attribute"""
        return self.name
    
    def get_pos(self):
        """Returns the peer's current position"""
        return self.pos
    
    def get_source_address(self):
        """Returns the peers's SOURCE_ADDRESS attribute"""
        return self.SOURCE_ADDRESS

    def log(self, message: str):
        """Logs a peer's message"""
        self.logger.info(message, extra={"peer_name": self.name, "round": self.round})

    def log_pos(self):
        """Logs the peer's position"""
        self.logger.info("Position: (%s, %s)", self.pos[0], self.pos[1], extra={"peer_name": self.name, "round": self.round})

    def start(self):
        """Enables the serving module of the peer"""
        serve_thread = threading.Thread(target=self.serve, args=())
        serve_thread.start()

    def scan_peers(self):
        """Queries the server which servers are within radio range"""
        scan_message = self.create_message("SCAN", f"{self.pos}|{self.RADIO_RANGE}")
        self.log("Scanning for peers")
        self.connect(self.SERVER_ADDRESS, "Server", scan_message)
        
    def remain_idle(self, seconds: int):
        """Simulates action pauses"""
        import time
        import random
        time.sleep(random.randint(1, seconds)) 

    def create_message(self, title: str, content="") -> Message:
        message = Message(
            title=title,
            round=self.round,
            name=self.name,
            source_address=self.SOURCE_ADDRESS,
            content=content
        )

        return message

    def serve(self):
        serve_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serve_socket.bind(self.SOURCE_ADDRESS)
        serve_socket.listen(3)
        serve_socket.settimeout(2)
        
        while self.serving_module_active:
            try:
                peer_socket, peer_address = serve_socket.accept()
                # self.log(f"Opened connection with {peer_address}")
                self.threadpool.add_task(self.receive, args=(peer_socket, peer_address, ))
            except socket.timeout:
                pass

        serve_socket.close()
        self.log("Terminating serving module")

    def receive(self, peer_socket:socket.socket, peer_address):
        peer_socket.settimeout(2)
        while self.serving_module_active:
            try:
                data = peer_socket.recv(1024)
                if not(data):
                    peer_socket.close()
                    # self.log(f"Closed connection with {peer_address}")
                    break
                message: Message = Message.decode(data)
                self.handle_message(message) 
            except socket.timeout:
                pass
     
    def handle_message(self, message: Message):
        """Checks the title of the message and takes the appropriate action
        
        - PASR (PASs Round): Increment round by one
        - OKMV (OK MoVe): The current move is legal. Proceed in changing the pos
        - DNMV (DeNy MoVe): The current move is illegal. Proceed to the next available
        move or declare to server that you will take no other move this round
        - FNMV (FiNish MoVe): Send after moving or having exhausted all movement options
        - PWIR (Peers WIthin Range): Shows which peers are withing radio range
        - TERM (TERMinate): Terminate the peer
        """
        title = message.get_title()
        peer_name = message.get_name()
        self.log(f"Received {title} message from {peer_name}")
        destination_address = message.get_source_address()
        content = message.get_content()

        if title == "PASR":
            self.round += 1
            self.log_pos()

            next_pos = self.select_move()
            message = self.create_message("RQMV", f"{self.pos}|{next_pos}")
            self.connect(destination_address, peer_name, message)
        elif title == "OKMV":
            self.pos = self.next_pos
            self.next_pos = None
            self.scan_peers()
            message = self.create_message("FNMV")
            self.connect(destination_address, peer_name, message)
        elif title == "DNMV":
            next_pos = self.select_move()
            if next_pos:
                message = self.create_message("RQMV", f"{self.pos}|{next_pos}")
            else:
                message = self.create_message("FNMV")
                self.scan_peers()
            self.connect(destination_address, peer_name, message)
        elif title == "PWIR":
            self.peers_in_vicinity = content
            peers = list(map(lambda t: t[0], self.peers_in_vicinity))
            self.log(f"Found: {peers} in vicinity")
        elif title == "TERM":
            self.round += 1
            self.serving_module_active = False
            self.log("Terminating")
        
    def select_move(self):
        """Selects a random combination of moves each round and tries to execute
        the first of them

        Returns:
            (tuple[int, int]/None): The next pos if a random direction is selected.
            If the random directions list is exhausted, it returns None
        """
        import random
        if not(self.next_pos):
            self.random_directions = random.sample(self.DIRECTIONS, random.randint(1, 4))

        if self.random_directions:
            random_direction = self.random_directions.pop()

            if random_direction == "up":
                self.next_pos = (self.pos[0], self.pos[1] + 1)
            elif random_direction == "down":
                self.next_pos = (self.pos[0], self.pos[1] - 1)
            elif random_direction == "left":
                self.next_pos = (self.pos[0] - 1, self.pos[1])
            else:
                self.next_pos = (self.pos[0] + 1, self.pos[1])

        else:
            self.next_pos = None
            self.log(f"Request to move to {self.next_pos}")

        return self.next_pos

    def connect(self, destination: tuple[str, int], recipient: str, message: Message):
        """Connect to the specific destination peer and deliver it a message
        
        Args:
            destination (tuple[str, int]): the address of the receiving peer
            recipient (str): receiving peer's name
            message (Message): the message to be sent
            
        """
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect(destination)
        # self.log(f"Open connection with {recipient}")
        self.send(peer_socket, recipient, message)

    def send(self, peer_socket: socket.socket, recipient: str, message: Message):
        encoded_message = message.encode()
        peer_socket.send(encoded_message)
        self.log(f"Send {message.get_title()} message to {recipient}")
        peer_socket.close()
        # self.log(f"Closed connection with {recipient}")


if __name__ == "__main__":
    import random
    import time
    peer = Peer("sf", (1, 2), 65433, 5)