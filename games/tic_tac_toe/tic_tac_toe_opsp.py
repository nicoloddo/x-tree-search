import pyspiel
import numpy as np

from src.game.game import Game

FREE_LABEL = ' '
class TicTacToe(Game):
    def __init__(self, players):
        _child_init_params = {
            'players': players,
        }
        self.players = players
        super().__init__(_child_init_params, players=players, main_action_space_id="board")
        self.state = self.gm.new_initial_state()
        
    def _game_model_definition(self):
        self._agents = np.array([[self.players[0].id, 'X'],
                                 [self.players[1].id, 'O']])
        self._action_spaces = {
            "board": lambda: self.opsp_state_to_action_space(self.state)
        }
        return pyspiel.load_game("tic_tac_toe")
    
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
        
        return board
    
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
    
    def get_current_player(self):
        return self.players[self.state.current_player()]
    
    def winner(self):
        if np.all(self.action_spaces["board"] != FREE_LABEL):
            return None
        else:
            return self.model.actions[-1]['who']
