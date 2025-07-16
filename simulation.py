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

def initialize_peers(max_peers: int, max_rounds: int, server_address: tuple[str, int], radio_range: int) -> list[Peer]:
    """Initiates peers, activates their serving module and main behavior
    
    Sets the initial positional of peers along the diagonal of the area
    Sets their ports from 61001 and onwards

    Args:
        max_peers (int): the maximum number of peers that will appear in the simulation
        max_rounds (int): the maximum rounds the simulation will run
        server_address (tuple[str, int]): the server's address and port
        radio_range (int): WiFi range

    Returns:
        (list[Peer]): the list of initiated peers
    """
    random_names_generator: "generator" = get_names()
    peers = []
    for i in range(max_peers):
        peer = Peer(next(random_names_generator), (i, i), 61001 + i, max_rounds, server_address, radio_range)
        threading.Thread(target=peer.start, args=()).start()
        peers.append(peer)
    return peers


def start_simulation(area_size: int, max_peers: int, max_rounds: int, radio_range: int):
    """Initiates the server and broadcasts the start of the simulation to all peers
    
    Args:
        area_size (int): the length (in units) of the side of the simulation area 
        max_peers (int): the maximum number of peers that will appear in the simulation
        max_rounds (int): the maximum rounds the simulation will run
        radio_range (int): WiFi range
        
    """
    server = Server(60000, area_size, max_peers, max_rounds)
    threading.Thread(target=server.start, args=()).start()
    peers = initialize_peers(MAX_PEERS, MAX_CYCLES, server.SERVER_ADDRESS, radio_range)
    server.bootstrap(peers)

if __name__ == "__main__":
    AREA_SIZE = 3
    MAX_PEERS = 2
    MAX_CYCLES = 20
    RADIO_RANGE = 2
    start_simulation(AREA_SIZE, MAX_PEERS, MAX_CYCLES, RADIO_RANGE)