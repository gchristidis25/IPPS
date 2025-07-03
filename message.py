import json

class Message:
    @classmethod
    def decode(cls, data: bytes):
        js: str = data.decode()
        payload: dict = json.loads(js)
        message = cls(
            title=payload["TITLE"],
            cycle=payload["CYCLE"],
            source_address=payload["SOURCE_ADDRESS"],
            content=payload["CONTENT"]
        )
        return message


    def __init__(self, title, cycle, source_address, content):
        self.data = {
            "TITLE": title,
            "CYCLE": cycle,
            "SOURCE": source_address,
            "CONTENT": content
        }

    def get_title(self):
        return self.data["TITLE"]
    
    def get_cycle(self):
        return self.data["CYCLE"]
    
    def get_source(self):
        return self.data["SOURCE"]
    
    def get_content(self):
        return self.data["CONTENT"]
    
