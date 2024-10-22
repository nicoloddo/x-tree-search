from abc import abstractmethod
from typing import Dict
import asyncio
import os
from IPython.display import clear_output

import numpy as np
import copy

from src.game.agents import User
from src.game.utils import parse_where_input as ut_parse_where_input
from src.game.game_model import GameModel
from src.game.game_tree import GameTree

import nest_asyncio
nest_asyncio.apply()

class Game:
    GameModel.verbose = False

    def __init__(self, child_init_params, *, players, main_action_space_id, ask_what=None, ask_where=None, what_question=None, where_question=None, parse_what_input=None, parse_where_input=None):
        self.child_init_params = child_init_params
        self.main_action_space_id = main_action_space_id

        self.gm = self._game_model_definition()
        self.players = {} # Dictionary that holds the players as 'id': player
        self._set_players(players)

        self.stop = False
        self._previous_state = None

        for player in self.players.values():
            if isinstance(player, User):
                if type(ask_what) is bool:
                    player.ask_what = ask_what
                if type(ask_where) is bool:
                    player.ask_where = ask_where

        self.what_question = what_question if what_question else "Insert what [insert 'exit' to exit] [click enter with no input to refresh]: "
        self.where_question = where_question if where_question else "Insert where [insert 'exit' to exit] [click enter with no input to refresh]: "
        self.parse_what_input = parse_what_input if parse_what_input else lambda what_str: what_str
        self.parse_where_input = parse_where_input if parse_where_input else lambda where_str: where_str

        self.gm.parse_what_input = self.parse_what_input
        self.gm.parse_where_input = self.parse_where_input

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