import subprocess

def run_log_terminal(name="None", round="None"):
    """Executes the logging process
    
    Args:
        name(str): the name of a specific peer
        round(int): the specified round of the simulation

    """
    subprocess.run(
        f'start "" cmd /c python "C:\\Users\\user\\OneDrive\\Υπολογιστής\\IPPS\\log.py" {name} {round}',
        shell=True
    )

def display_interface():
    """Displays the interface of the logging process"""
    print("Press 1 to select peer")
    print("Press 2 to select round")
    print("Press 3 to select peer and round")
    print("Press q to exit")
    print()

def main():
    """Executes the basic logging loop
    
    Selecting `1` will show the logs of the specified peer
    Selecting `2` will show all the logs that happened during the specified round
    Selecting `3` will show all the logs of specified peer during the specified round
    Selecting `q` will quit the loop
    Selecting anything else has no effect and restarts the loop

    """
    while True:
            display_interface()
            input_action = input("Select an action: ")
            if input_action == "1":
                input_name = input("Select a name: ")
                run_log_terminal(name=input_name)
            elif input_action == "2":
                input_round = input("Select a round: ")
                run_log_terminal(round=input_round)
            elif input_action == "3":
                input_name = input("Select a name: ")
                input_round = input("Select a round: ")
                run_log_terminal(name=input_name, round=input_round)
            elif input_action == "q":
                exit()
            else:
                print("This is not an appropriate action")
                print()

if __name__ == "__main__":
    main()