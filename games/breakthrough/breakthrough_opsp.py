import pyspiel
import numpy as np
import string

from games.breakthrough import Breakthrough
from src.game.agents import User
from games.common.utils import AutoCallDict

FREE_LABEL = ' '
class BreakthroughOpSp(Breakthrough):
    @classmethod
    def state_translator(cls, opsp_state):
        # Convert the state string into a 2D list
        board_str = str(opsp_state)
        # Split into rows, remove the last 2 lines (column labels + last \n)
        rows = board_str.split('\n')[:-2]
        # Remove the row numbers from each line
        rows = [row[1:] for row in rows]

        # Create the board representation
        board = []
        for row in rows:
            current_row = []
            for cell in row:
                if cell == '.':
                    current_row.append(FREE_LABEL)
                elif cell == 'w':
                    current_row.append('w')
                elif cell == 'b':
                    current_row.append('b')
            board.append(current_row)
        
        return np.array(board)
    
    def coordinates_to_breakthrough_string(self, coordinates):
        row, col = coordinates
        # Convert column number to letter (0 -> a, 1 -> b, etc.)
        col_letter = string.ascii_lowercase[col]
        # Invert row number (0 -> 8, 1 -> 7, etc. for 8x8 board)
        row_number = self.board_side_size - row
        return f"{col_letter}{row_number}"
        
    def _game_model_definition(self):
        game = pyspiel.load_game("breakthrough", {"rows": 6, "columns": 6})
        self.state = game.new_initial_state()
        self._agents = np.array([['b'],
                                 ['w']])
        self.board_side_size = self.state_translator(self.state).shape[0]

        from games.breakthrough.interface.gradio_interface import BreakthroughGradioInterface
        BreakthroughGradioInterface.coordinates_to_string = self.coordinates_to_breakthrough_string
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
        old_coordinates = action['where']
        new_coordinates = action['what']

        breakthrough_old_coords = self.coordinates_to_breakthrough_string(old_coordinates)
        breakthrough_new_coords = self.coordinates_to_breakthrough_string(new_coordinates)
        action_str = f"{breakthrough_old_coords}{breakthrough_new_coords}"

        legal_actions = self.state.legal_actions(player)
        action_found = False
        for action in legal_actions:
            available_action_str = self.state.action_to_string(player, action)[:4] # Cut extra characters identifying captures for example
            if available_action_str == action_str:
                action_found = True
                break
        
        if action_found:
            self.state.apply_action(action) # The last action of the iteration is the one where the for was broken
        else:
            raise ValueError(f"The action {action_str} is not legal. Available actions are: {[self.state.action_to_string(player, action) for action in legal_actions]}")
    
    def winner(self):
    # TODO: Base the winner inference on state.player_return
        if not self.ended:
            return None
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
