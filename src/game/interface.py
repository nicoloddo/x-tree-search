from abc import ABC, abstractmethod

class GameInterface(ABC):
    def __init__(self, game):
        self.started = False
        self.game = game

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
