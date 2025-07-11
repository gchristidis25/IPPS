import json

class Message:
    """A message form for peers to exchange information
    
    Attributes:
        data (dict): the dictionary with all the message features
            - title (str): the title of the message
            - round (int): the current round the peer is
            - name (int): the name of the peer
            - source_address (tuple[str, int]): the address the peer actively listens to
            - content (str): the rest of the message's content

    """

    @classmethod
    def decode(cls, data: bytes) -> "Message":
        """Decodes datastream into a Message format"""
        js: str = data.decode()
        payload: dict = json.loads(js)
        message: Message = cls(
            title=payload["TITLE"],
            round=payload["ROUND"],
            name=payload["NAME"],
            source_address=tuple(payload["SOURCE_ADDRESS"]),
            content=payload["CONTENT"]
        )
        return message


    def __init__(
            self,
            title: str,
            round: int,
            name: str,
            source_address: tuple[str, int],
            content: str
            ):
        self.data = {
            "TITLE": title,
            "ROUND": round,
            "NAME": name,
            "SOURCE_ADDRESS": source_address,
            "CONTENT": content
        }

    def get_title(self) -> str:
        """Returns the message's title attribute"""
        return self.data["TITLE"]
    
    def get_round(self) -> int:
        """Returns the message's round attribute"""
        return self.data["ROUND"]
    
    def get_name(self) -> str:
        """Returns the message's name attribute"""
        return self.data["NAME"]
    
    def get_source_address(self) -> tuple[str, int]:
        """Returns the message's source_address attribute"""
        return self.data["SOURCE_ADDRESS"]
    
    def get_content(self) -> str:
        """Returns the message's content attribute"""
        return self.data["CONTENT"]
    
    def encode(self) -> bytes:
        """Encodes the message"""
        js = json.dumps(self.data)
        return js.encode()
    
if __name__ == "__main__":
    a = Message("AAAA", 1, "Olivia", ("127.0.0.1", 65432), "(1, 2)|(2, 3)").encode()
    b = Message.decode(a)
    print(b.get_content())
