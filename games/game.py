from abc import abstractmethod
from typing import Dict
import asyncio

from src.game.game_model import GameModel
from src.game.game_tree import GameTree

class Game:
    GameModel.verbose = False

    def __init__(self):
        self.gm = self._game_model_definition()
        self.players = {}
        self.stop = False

    @abstractmethod
    def _game_model_definition(self) -> GameModel:
        """Method that builds the game model of the game."""
        pass

    @property
    def model(self):
        return self.gm
    
    @property
    def tree(self):
        return GameTree(self.gm, "board")

    @abstractmethod
    def act(self, action) -> None:
        pass
    
    def set_players(self, players):
        self.players = players

    def start(self):
        """This does not run on Jupyter"""
        asyncio.run(self._start_game())
    
    def start_on_jupyter(self):
        return asyncio.ensure_future(self._start_game())

        # If you're in a Jupyter notebook, you can start the game like this:
        # await game.start_on_jupyter()

    async def _start_game(self): 
        print(self.tree.get_current_state().state)

        while not self.gm.ended and not self.stop:
            
            await asyncio.gather(*(player.play(self) for player in self.players))

            # Add a small delay here to prevent busy-waiting
            await asyncio.sleep(0.05)
        
        print("Game stopped or ended")

class GameAgent:
    def __init__(self, core, *, agent_id):
        self.core = core
        self.id = agent_id

    async def play(self, game):
        # Use the search algorithm to determine the best move
        tree = game.tree

        current_state = tree.get_current_state()

        best_outcome_id, _ = self.core.run(tree, current_state.id, with_constraints={'who': self.id})
        
        if best_outcome_id is None:
            return
        
        best_outcome = tree.get_node(best_outcome_id)
        action = best_outcome.action
        
        # Apply the move to the game
        if action is not None:
            game.act(action)

class User:
    def __init__(self, *, agent_id, ask_what=True, ask_where=True):
        self.id = agent_id
        self.ask_what = ask_what
        self.ask_where = ask_where

    async def play(self, game):
        who = self.id

        if self.ask_what:
            what = await self.async_input("Insert what [insert 'exit' to exit]: ")

            if what == 'exit':
                game.stop = True
                return
        else:
            what = ''
        
        if self.ask_where:
            where_str = await self.async_input("Insert where (format: x,y) [insert 'exit' to exit]: ")
            
            if where_str == 'exit':
                game.stop = True
                return
            
            try:
                x, y = map(int, where_str.split(','))
                where = (x, y)
            except ValueError:
                print("Invalid input format. Please use 'x,y' format.")
                return await self.async_input("Insert where (format: x,y) [insert 'exit' to exit]: ")
        else:
            where = ''
        
        action = {'who': who, 'where': where, 'what': what}
        game.act(action)

    async def async_input(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)