import socket
import threading
import log
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
    
    """
    def __init__(self, name: str, pos: tuple[int, int], server_port: int, END_ROUND):
        self.logger = log.create_logger()
        self.name: str = name
        self.pos: tuple[int, int] = pos
        self.SOURCE_ADDRESS: tuple[str, int] = ("127.0.0.1", server_port)
        self.round: int = 0
        self.END_ROUND: int = END_ROUND
        self.DIRECTIONS: list[str] = ["up", "down", "left", "right"]
        self.random_directions: list[str] = []
        self.next_pos: tuple[int, int] = None

    def get_name(self):
        """Returns the peer's name attribute"""
        return self.name
    
    def get_source_address(self):
        """Returns the peers's SOURCE_ADDRESS attribute"""
        return self.SOURCE_ADDRESS

    def log(self, message: str):
        """Logs a peer's message up until END_ROUND"""
        if self.round < self.END_ROUND:
            self.logger.info(message, extra={"peer_name": self.name, "round": self.round})

    def log_pos(self):
        """Logs the peer's position up until END_ROUND"""
        if self.round < self.END_ROUND:
            self.logger.info("Position: (%s, %s)", self.pos[0], self.pos[1], extra={"peer_name": self.name, "round": self.round})

    def remain_idle(self, seconds: int):
        """Simulates action pauses"""
        import time
        import random
        time.sleep(random.random(seconds) + 1) 

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
        serve_socket.listen(5)
        
        while True:
            peer_socket, peer_address = serve_socket.accept()
            # self.log(f"Opened connection with {peer_address}")
            threading.Thread(target=self.receive, args=(peer_socket, peer_address)).start()


    def receive(self, peer_socket, peer_address):
        while True:
            data = peer_socket.recv(1024)
            if not(data):
                peer_socket.close()
                # self.log(f"Closed connection with {peer_address}")
                break

            message: Message = Message.decode(data)
            threading.Thread(target=self.handle_message, args=(message,)).start()
                

    def handle_message(self, message: Message):
        """Checks the title of the message and takes the appropriate action
        
        - PASR (PASs Round): Increment round by one and take next move action
        - OKMV (OK MoVe): The current move is legal. Proceed in changing the pos
        - DNMV (DeNy MoVe): The current move is illegal. Proceed to the next available
        move or declare to server that you will take no other move this round
        """
        title = message.get_title()
        peer_name = message.get_name()
        self.log(f"Received {title} message from {peer_name}")
        destination_address = message.get_source_address()
        if title == "PASR":
            self.round += 1
            self.log_pos()
            threading.Thread(target=self.select_move, args=(destination_address, peer_name, )).start()
        elif title == "OKMV":
            self.pos = self.next_pos
            self.next_pos = None
        elif title == "DNMV":
            threading.Thread(target=self.select_move, args=(destination_address, peer_name, )).start()
            
        
    def select_move(self, destination_address, recipient):
        """Selects a random combination of moves each round and tries to execute the first of them

        If the move is illegal, it goes to the next available move.
        If the range of preselected moves is exhausted, then it stays in the same pos
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

            self.log(f"Request to move to {self.next_pos}")
            request_move_message = self.create_message("RQMV", f"{self.pos}|{self.next_pos}")
            threading.Thread(target=self.connect, args=(destination_address, recipient, request_move_message, )).start()
        else:
            self.next_pos = None
            finished_move_message = self.create_message("FNMV")
            threading.Thread(target=self.connect, args=(destination_address, recipient, finished_move_message)).start()

    def connect(self, destination: tuple[str, int], recipient: str, message: Message):
        """Connect to the specific destination peer and deliver it a message
        
        Args:
            destination (tuple[str, int]): the address of the receiving peer
            recipient (str): receiving peer's name
            message (Message): the message to be sent
            
        """
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect(destination)
        self.log(f"Open connection with {recipient}")
        threading.Thread(target=self.send, args=(peer_socket, recipient, message, )).start()

    def send(self, peer_socket: socket.socket, recipient: str, message: Message):
        encoded_message = message.encode()
        peer_socket.send(encoded_message)
        self.log(f"Send {message.get_title()} message to {recipient}")
        peer_socket.close()
        self.log(f"Closed connection with {recipient}")


if __name__ == "__main__":
    import random
    import time
