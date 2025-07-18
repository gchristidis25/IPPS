from server import Server
from peer import Peer
from pathlib import Path
from threadpool import Threadpool
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

def initialize_peers(max_peers: int, max_rounds: int, server_address: tuple[str, int], radio_range: int, threads: int) -> list[Peer]:
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
        peer = Peer(next(random_names_generator), (i, i), 61001 + i, max_rounds, server_address, radio_range, threads)
        peer.start()
        # threading.Thread(target=peer.start, args=()).start()
        peers.append(peer)
    return peers


def start_simulation(area_size: int, max_peers: int, max_round: int, radio_range: int, num_threads: int):
    """Handles the simulation of a p2p network using the IPPS algorithm
    
    Args:
        area_size (int): the length (in units) of the side of the simulation area 
        max_peers (int): the maximum number of peers that will appear in the simulation
        max_round (int): the maximum round the simulation will run
        radio_range (int): WiFi range
        
    """
    threadpool = Threadpool(num_threads)
    server: Server = Server(60000, area_size, max_peers, max_round, threadpool)
    server.start()
    peers = initialize_peers(max_peers, max_round, server.SERVER_ADDRESS, radio_range, threadpool)
    server.bootstrap(peers)

    while True:
        if server.get_round() == max_round:
            # wait some time for the peers to process the TERM messages
            import time
            time.sleep(3)
            threadpool.terminate()
            break

    print("End")

if __name__ == "__main__":
    AREA_SIZE = 10
    MAX_PEERS = 10
    MAX_ROUND = 10
    RADIO_RANGE = 2
    THREADPOOL_THREADS = MAX_PEERS
    # import cProfile
    # import pstats
    # profiler = cProfile.Profile()
    # profiler.enable()

    start_simulation(AREA_SIZE, MAX_PEERS, MAX_ROUND, RADIO_RANGE, THREADPOOL_THREADS)

    # profiler.disable()
    # stats = pstats.Stats(profiler)
    # stats.sort_stats("cumulative")
    # stats.print_stats(10)