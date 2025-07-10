import logging
from pathlib import Path
import logging
from datetime import datetime
import sys

class CustomFormatter(logging.Formatter):
    """A custom formatter that logs microseconds in the datefmt"""

    def formatTime(self, record: logging.LogRecord, datefmt=None) -> str:
        """Extends the time format to include microseconds
        
         Args:
            record (logging.LogRecord): The log record containing the timestamp.
            datefmt (str): A custom datetime format string.

        Returns:
            (str): The formatted time string

        """
        ct: datetime = datetime.fromtimestamp(record.created)
        timestamp: str
        if datefmt:
            timestamp = ct.strftime(datefmt)
        else:
            timestamp = ct.strftime('%Y-%m-%d %H:%M:%S.%')
        return timestamp
    
def create_logger() -> logging.Logger:
    """Create a custom logger that saves logs in the `log.txt` file
    
    Returns:
        (logging.Logger): the custom logger
    """
    logger = logging.getLogger("SIM")
    logger.setLevel(logging.INFO)
    formatter = CustomFormatter('%(levelname)s - %(asctime)s - [peer_name=%(peer_name)s] - [round=%(round)s] - %(message)s', datefmt='%H:%M:%S:%f')
    handler = logging.FileHandler("log.txt", "w")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_logfile() -> "generator":
    """Creates a generator that yields logs from the `log.txt` file
    
    Yields:
        (str): the next log line from the `log.txt` file

    """
    filepath: Path = Path(__file__).parent.joinpath("log.txt")
    with open(filepath, "r") as file:
        lines: list[str] = file.readlines()
        for line in lines:
            line = line.strip()
            yield line

def preety_parser(log: str, input_name: str, input_round: int):
    """Applies a specific format, colors appropriately each section of the log" and prints it
    
    ARGS:
        log (str): the logging line from `log.txt`
        input_name (str): if specified, prints the log if only it corresponds to that peer,
        otherwise it prints logs from all peers
        input_round (int): if specified, prints the log if only it corresponds to that round,
        otherwise it prints logs from all rounds
        
    """
    RESET = "\033[0m"
    MAGENTA = "\x1b[35m"
    GREEN = '\033[92m'
    YELLOW = '\033[93m'

    [type, time, name, round, message] = [item.strip(" []") for item in log.split(" - ")]
    # eg name = Alex --> Alex
    # eg round = 1 --> 1
    round: str = round.split("=")[1]
    name: str = name.split("=")[1]

    if (input_name == None and input_round == None) or \
       (input_name == name and input_round == None) or \
       (input_name == None and input_round == round) or \
       (input_name == name and input_round == round):
        time: str = f"{MAGENTA}{time}{RESET}"
        round: str = f"{YELLOW}{round}{RESET}"
        name: str = f"{GREEN}{name}{RESET}"

        log: str = f"{time} - {round} - {name}: {message}"
        print(log)

def display_logfile(name=None, round=None):
    """Prints the logfile. If name and round are specified, it filters the logs to include only them"""
    logfile: "generator" = get_logfile()
    for log in logfile:
        preety_parser(log, input_name=name, input_round=round)


if __name__ == "__main__":
    #required for `log_parser`
    input_name = sys.argv[1]
    if input_name == "None":
        input_name = None

    input_round = sys.argv[2]
    if input_round == "None":
        input_round = None

    display_logfile(name=input_name, round=input_round)

    import os
    os.system("pause") 



