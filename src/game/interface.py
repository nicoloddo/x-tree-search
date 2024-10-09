from abc import ABC, abstractmethod

class GameInterface(ABC):
    def __init__(self):
        self.started = False

    @abstractmethod
    def start(self):
        # Set started to True
        self.started = True
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def output(self, text: str):
        pass
