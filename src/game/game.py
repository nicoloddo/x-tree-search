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

    def __init__(self, child_init_params, *, players, main_action_space_id):
        self.child_init_params = child_init_params
        self.main_action_space_id = main_action_space_id

        self.gm = self._game_model_definition()
        self.players = {} # Dictionary that holds the players as 'id': player
        self._set_players(players)

        self.stop = False
        self.clear_console = self.clear_cmd  # To keep track of the previous state
        self._previous_state = None

    def restart(self):
        """
        Restart the game by creating a new instance with the same initialization parameters.
        """
        # Create a new instance of the child class: __class__ is the class of the current instance
        new_game = self.__class__(**self.child_init_params)
        
        # Transfer any necessary attributes from the old game to the new game
        new_game.interface = self.interface
        
        # Replace the current instance with the new one
        self.__dict__.update(new_game.__dict__)
        
        return self
    
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
        return GameTree(self.gm, self.main_action_space_id, self.action_print_attributes())
    
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

    @abstractmethod
    def act(self, action) -> None:
        pass
    
    def _set_players(self, players):
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