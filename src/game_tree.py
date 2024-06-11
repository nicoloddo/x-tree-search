from src.tree import Tree
from src.game_model import GameModel

class GameTree(Tree):
    def __init__(self, game):
        super().__init__()
        if not isinstance(game, GameModel):
            raise ValueError("The game of the GameTree must be a valid GameModel object.")
        self.game = game # Add root node

    # TODO:
    ''' Make function to expand nodes based on what is possible to do inside the game. Use it inside minmax '''