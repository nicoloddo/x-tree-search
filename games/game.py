from abc import abstractmethod
from typing import Dict

from src.game.game_model import GameModel
from src.game.game_tree import GameTree

class Game:
    GameModel.verbose = False

    def __init__(self):
        self.gm = self._game_model_definition()
        self.gmt = self._game_tree_definition()

    @abstractmethod
    def _game_model_definition(self) -> GameModel:
        """Method that builds the game model of the game."""
        pass

    @abstractmethod
    def _game_tree_definition(self) -> GameTree:
        """Method that builds and returns the base game tree. 
        It is executed after the game model definition."""
        pass

    @property
    def model(self):
        return self.gm
    
    @property
    def tree(self):
        return self.gmt

    @abstractmethod
    def act(self, agent, move) -> None:
        pass