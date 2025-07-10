def string_to_tuple(s: str) -> tuple[int, int]:
    """Takes a string and turns it into a tuple

    Args:
        s (str): the string must have format `(x, y)` where x and y are integers
    
    Returns:
        (tuple[int, int]): the tuple form of the s argument

    """
    s = s.strip("()")
    t: tuple[int, int] = tuple(map(int, s.split(",")))

    return t

if __name__ == "__main__":
    print(type(string_to_tuple("[1, 2]")))
    print(string_to_tuple("[1, 2]"))