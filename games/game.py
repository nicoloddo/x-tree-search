from abc import abstractmethod
from typing import Dict

from src.game.game_model import GameModel
from src.game.game_tree import GameTree

class GameAgent:
    def __init__(self, search_algorithm, *, agent_id):
        self.search_algorithm = search_algorithm
        self.id = agent_id

    async def play(self, game):
        while not game.is_over():
            # Use the search algorithm to determine the best move
            current_state = game.tree.get_current_state(from_player_perspective = self.id)
            best_outcome_id = self.search_algorithm.run(current_state.id)
            best_outcome = game.tree.get_node(best_outcome_id)

            action = best_outcome.action
            
            # Apply the move to the game
            game.act(action)
            
            # Simulate some processing time
            await asyncio.sleep(0.1)
        
        print(f"Agent finished playing. Final score: {game.get_score()}")

class Game:
    GameModel.verbose = False

    def __init__(self):
        self.gm = self._game_model_definition()
        self.gmt = self._game_tree_definition()
        self.players = {}

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
    def act(self, action) -> None:
        pass
    
    def add_player(self, player : GameAgent, *, player_id : str):
        self.players[player_id] = player

    def start_game(self, players):
        for player in players:
            player.play(self)