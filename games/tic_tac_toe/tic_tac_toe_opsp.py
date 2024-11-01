import pyspiel
import numpy as np

from games.tic_tac_toe import TicTacToe
from src.game.agents import User
from games.common.utils import AutoCallDict

FREE_LABEL = ' '
class TicTacToeOpSp(TicTacToe):
    @classmethod
    def state_translator(cls, opsp_state):
        # Convert the state string into a 2D list
        board_str = str(opsp_state)
        rows = board_str.split('\n')
        
        # Create the board representation
        board = []
        for row in rows:
            current_row = []
            for cell in row:
                if cell == '.':
                    current_row.append(FREE_LABEL)
                elif cell == 'x':
                    current_row.append('X')
                elif cell == 'o':
                    current_row.append('O')
            board.append(current_row)
        
        return np.array(board)
        
    def _game_model_definition(self):
        game = pyspiel.load_game("tic_tac_toe")
        self.state = game.new_initial_state()
        self._agents = np.array([['X'],
                                 ['O']])
        return game

    def act(self, action=None, *, opsp_action=None, player=None) -> None:

        if opsp_action is not None:
            if player is None:
                raise SyntaxError("When providing an opsp action you need to provide the player id as well.")
            self.last_player = player
            self.state.apply_action(opsp_action)
            return
        else:
            if action is None:
                raise ValueError("No action to perform was given.")
        
        player = action['who']
        self.last_player = player
        coordinates = action['where']

        if player == 0:
            sign = 'x'
        elif player == 1:
            sign = 'o'
        else:
            raise ValueError("Player variable has to be 0 or 1")
        
        action_str = f"{sign}({coordinates[0]},{coordinates[1]})"

        legal_actions = self.state.legal_actions(player)
        action_found = False
        for action in legal_actions:
            available_action_str = self.state.action_to_string(player, action)
            if available_action_str == action_str:
                action_found = True
                break
        
        if action_found:
            self.state.apply_action(action)
        else:
            raise ValueError(f"The action {action_str} is not legal. Available actions are: {[self.state.action_to_string(player, action) for action in legal_actions]}")
    
    def winner(self):
        if not self.ended:
            return None
        if np.all(self.action_spaces["board"] != FREE_LABEL):
            return None
        else:
            return self.last_player

    """General overrides for OpSp game classes:"""
    @property
    def started(self):
        return self.state.serialize() == self.model.new_initial_state().serialize()
    
    @property
    def ended(self):
        return self.state.current_player() == pyspiel.PlayerId.TERMINAL
    
    @property
    def action_spaces(self):
        return AutoCallDict({
            "board": lambda: self.state_translator(self.state)
        })
    
    @property
    def agents(self):
        return self._agents
    
    def get_current_player(self):
        return self.players[self.state.current_player()]
