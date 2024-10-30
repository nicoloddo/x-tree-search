import pyspiel
import numpy as np

from games.tic_tac_toe import TicTacToe
from src.game.agents import User

class AutoCallDict(dict):
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if callable(value):
            return value()
        return value

FREE_LABEL = ' '
class TicTacToeOpSp(TicTacToe):
        
    def _game_model_definition(self):
        game = pyspiel.load_game("tic_tac_toe")
        self.state = game.new_initial_state()
        self._agents = np.array([[self.players[0].id, 'X'],
                                 [self.players[1].id, 'O']])
        self._action_spaces = AutoCallDict({
            "board": lambda: self.opsp_state_to_action_space(self.state)
        })
        return game
    
    def opsp_state_to_action_space(self, opsp_state):
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
    
    @property
    def started(self):
        return self.state.serialize() == self.gm.new_initial_state().serialize()
    
    @property
    def ended(self):
        return self.state.is_terminal()

    @property
    def model(self):
        return self.gm
    
    @property
    def action_spaces(self):
        return self._action_spaces
    
    @property
    def agents(self):
        return self._agents

    def act(self, action, manual_insert = False) -> None:
        player = action['who']
        coordinates = action['where']

        if not isinstance(self.players[player], User) and not manual_insert:
            raise ValueError("Only users can utilize the act method in TicTacToeOpSp.")

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
    
    def get_current_player(self):
        return self.players[self.state.current_player()]
    
    def winner(self):
        if np.all(self.action_spaces["board"] != FREE_LABEL):
            return None
        else:
            return self.model.actions[-1]['who']
