from abc import ABC, abstractmethod

class GameInterface(ABC):
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def output(self, text: str):
        pass
