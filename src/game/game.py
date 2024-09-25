from abc import abstractmethod
from typing import Dict
import asyncio
import os
from IPython.display import clear_output

import numpy as np
import copy

from src.game.game_model import GameModel
from src.game.game_tree import GameTree

import nest_asyncio
nest_asyncio.apply()

class Game:
    GameModel.verbose = False

    def __init__(self):
        self.gm = self._game_model_definition()
        self.players = {} # Dictionary that holds the players as 'id': player
        self.stop = False
        self.clear_console = self.clear_cmd  # To keep track of the previous state
        self._previous_state = None

    @property
    def started(self):
        return self.gm.started
    
    @property
    def ended(self):
        return self.gm.ended

    @property
    def model(self):
        return self.gm
    
    @property
    def tree(self):
        return GameTree(self.gm, "board", self.action_print_attributes())
    
    @abstractmethod
    def _game_model_definition(self) -> GameModel:
        """Method that builds the game model of the game."""
        pass

    @abstractmethod
    def expansion_constraints_self(self) -> Dict:
        """Method that provides constraints to expand a node of the tree
        game when is the turn of the self player.
        Return None if you don't want to constrain the expansion.
        E.g.: 
        expansion_constraints_self(self, maximizer_id) 
            return {'who': maximizer_id}"""
        pass
    
    @abstractmethod
    def expansion_constraints_other(self) -> Dict:
        """Method that provides constraints to expand a node of the tree
        game when is the turn of the other player.
        Return None if you don't want to constrain the expansion.
        E.g.: 
        expansion_constraints_other(self, agent_id) 
            not_agent_ids = [key for key, val in self.players.items() if val != agent_id]
            other_id = not_agent_ids[0]
            return {'who': other_id}
        """
        pass

    def action_print_attributes(self):
        """Which attributes to print when printing an action"""
        return ['who', 'what', 'where', 'on', 'what_before']

    def act(self, action):
        args = self._act(action)
        self.model.action(*args)

    @abstractmethod
    def _act(self, action) -> None:
        pass
    
    def set_players(self, players):
        for player in players:
            self.players[player.id] = player
    
    def winner(self):
        """Method to determine the winner of the game.
        Override in the specific game if you want to change its way of determining the winner."""
        return None

    """Interface methods"""
    #TODO: Make separate Interface class for these methods
    def start(self):
        self.clear_console = self.clear_cmd
        self.update_display = self.print_state
        asyncio.run(self._start_game())
    
    def print_state(self, current_state):
        """Override in the specific game if you want to change its way of display"""
        print(current_state)

    async def _start_game(self):
        # Start the state monitoring task
        self.stop = False
        state_monitoring_task = asyncio.create_task(self._monitor_game_state())

        print(self.tree.get_current_state().state)

        while not self.gm.ended and not self.stop:
            await asyncio.gather(*(player.play(self) for player in self.players.values()))
            await asyncio.sleep(0.1)  # Reduced sleep time for more responsive updates

        # Stop the state monitoring task
        state_monitoring_task.cancel()

        print()
        if self.stop:
            print("Game paused.")
        elif self.gm.ended:
            print("Game finished.")
        print()
        print(self.tree.get_current_state().state)

    async def _monitor_game_state(self):
        """Periodically checks the game's current state and prints it if it has changed."""
        while not self.gm.ended and not self.stop:
            current_state = self.tree.get_current_state().state

            if not np.array_equal(current_state, self._previous_state):
                self.clear_console()
                self.update_display(current_state)
                self._previous_state = copy.deepcopy(current_state)
            
            await asyncio.sleep(0.2)  # Adjust the sleep time as needed
    
    def clear_cmd(self):
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console

class GameAgent:
    def __init__(self, *, core, agent_id):
        self.core = core
        self.id = agent_id

    async def play(self, game):
        await asyncio.sleep(0.1)
        if game.gm.ended:
            return
    
        # Use the search algorithm to determine the best move        
        tree = game.tree

        current_state = tree.get_current_state()
        self_constraints = game.expansion_constraints_self(self.id)
        other_constraints = game.expansion_constraints_other(self.id)
        best_outcome, _ = self.core.run(current_state, expansion_constraints_self=self_constraints, expansion_constraints_other=other_constraints)
        
        if best_outcome is None:
            return
        
        action = best_outcome.action
        
        # Apply the move to the game
        if action is not None:
            await asyncio.to_thread(game.act, action)
    
    @property
    def choice(self):
        return self.core.last_choice

class User:
    def __init__(self, *, agent_id, jupyter_interactive=False, ask_what=True, ask_where=True, pause_first_turn=False):
        self.id = agent_id
        self.jupyter_interactive = jupyter_interactive
        self.ask_what = ask_what
        self.ask_where = ask_where
        self.pause_first_turn = pause_first_turn

    async def play(self, game):
        if game.interface_mode == 'jupyter':
            return
        
        if self.pause_first_turn:
            game.stop = True
            return

        await asyncio.sleep(1)
        if game.gm.ended:
            return
       
        who = self.id

        if self.ask_what:
            what = await self.async_input("Insert what [insert 'exit' to exit] [click enter with no input to refresh]: ")

            if what == 'exit':
                game.stop = True
                return
            if what == '':
                await asyncio.sleep(0.5)
        else:
            what = ''
        
        if self.ask_where:
            where_input_question = "Insert where (format: x,y) [insert 'exit' to exit] [click enter with no input to refresh]: "
            where_str = await self.async_input(where_input_question)
            
            if where_str == 'exit':
                game.stop = True
                return
            elif where_str == '':
                await asyncio.sleep(0.5)
                return await self.async_input(where_input_question)
            else:
                try:
                    x, y = map(int, where_str.split(','))
                    where = (x, y)
                except ValueError:
                    print("Invalid input format. Please use 'x,y' format.")
                    return await self.async_input(where_input_question)
        else:
            where = ''
        
        action = {'who': who, 'where': where, 'what': what}
        await asyncio.to_thread(game.act, action)

    async def async_input(self, prompt: str) -> str:
        # Ensure proper input handling in Jupyter
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)