from server import Server
from peer import Peer
from pathlib import Path
import threading

def get_names() -> "generator":
    """Creates a generator that yields names from `random_names.txt` file
    
    Yields:
        (str): a name from the `random_names.txt` file
    
    """
    filepath: Path = Path(__file__).parent.joinpath("random_names.txt")
    with open(filepath, "r") as file:
        names: list[str] = file.readlines()
        for name in names:
            name = name.strip()
            yield name

def initialize_peers(max_peers: int, max_rounds: int, server_address: tuple[str, int]) -> list[Peer]:
    """Initiates peers, activates their serving module and main behavior
    
    Sets the initial positional of peers along the diagonal of the area
    Sets their ports from 61001 and onwards

    Args:
        max_peers (int): the maximum number of peers that will appear in the simulation
        max_rounds (int): the maximum rounds the simulation will run
        server_address (tuple[str, int]): the server's address and port

    Returns:
        (list[Peer]): the list of initiated peers
    """
    random_names_generator: "generator" = get_names()
    peers = []
    for i in range(max_peers):
        peer = Peer(next(random_names_generator), (i+1, i+1), 61001 + i, max_rounds, server_address)
        threading.Thread(target=peer.start, args=()).start()
        peers.append(peer)

    return peers


def start_simulation(area_size: int, max_peers: int, max_rounds: int):
    """Initiates the server and broadcasts the start of the simulation to all peers
    
    Args:
        area_size (int): the length (in units) of the side of the simulation area 
        max_peers (int): the maximum number of peers that will appear in the simulation
        max_rounds (int): the maximum rounds the simulation will run
        
    """
    server = Server(60000, area_size, max_peers, max_rounds)
    threading.Thread(target=server.serve, args=()).start()
    peers = initialize_peers(MAX_PEERS, MAX_CYCLES, server.SERVER_ADDRESS)
    server.start(peers)

if __name__ == "__main__":
    AREA_SIZE = 10
    MAX_PEERS = 3
    MAX_CYCLES = 20
    start_simulation(AREA_SIZE, MAX_PEERS, MAX_CYCLES)