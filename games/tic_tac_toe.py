from typing import Dict

import numpy as np

from games.game import Game, GameModel, GameTree

import ipywidgets as widgets
from IPython.display import display, HTML
import asyncio

FREE_LABEL = ' '
class TicTacToe(Game):

    def action_print_attributes(self):
        """Which attributes to print when printing an action"""
        return ['what', 'where']
    
    def expansion_constraints_self(self, agent_id):
        return {'who': agent_id}
    
    def expansion_constraints_other(self, agent_id):
        not_agent_ids = [key for key in self.players.keys() if key != agent_id] # Get the players ids different than the maximizer
        if len(not_agent_ids) == 1:
            other_id = not_agent_ids[0]
            return {'who': other_id}
        else:
            raise ValueError("A TicTacToe game should have a maximum of two players.")
    
    def _game_model_definition(self) -> GameModel:
        gm = GameModel( 
        agents_number=2, default_agent_features=['not starter', 'X'], additional_agent_features=[['starter'], ['O']], 
        agent_features_descriptions="2 players with feature 1 indicating who is starting, and feature 2 indicating their symbol.",
        game_name="tic-tac-toe")
        gm.add_action_space("board", dimensions=[3, 3], default_labels=[FREE_LABEL], additional_labels=[['X', 'O']], dimensions_descriptions="3x3 board.")

        # Disable actions on the agent feature space.
        gm.disable_actions(on="agent")
        gm.agents[1, 1] = 'O'
        gm.agents[1, 0] = 'starter'

        # Set Endgame
        def tic_tac_toe_endgame(game):
            board = game.action_spaces["board"]
            # Check rows for winning condition
            for row in board:
                if row[0] == row[1] == row[2] != FREE_LABEL:
                    return True

            # Check columns for winning condition
            for col in range(3):
                if board[0][col] == board[1][col] == board[2][col] != FREE_LABEL:
                    return True

            # Check diagonals for winning condition
            if board[0][0] == board[1][1] == board[2][2] != FREE_LABEL:
                return True
            if board[0][2] == board[1][1] == board[2][0] != FREE_LABEL:
                return True
            
            full_board = np.all(board != FREE_LABEL)
            if full_board:
                return True

            # If no winner and not full_board, return False
            return False

        gm.set_endgame(tic_tac_toe_endgame)

        # Set rules
        gm.action_is_violation_if(lambda who, where, what, game: not game.started and game.agents[who][0] != 'starter', rule_description="This is not the starting player and this is the first turn.")
        gm.action_is_violation_if(lambda who, where, what, game: game.started and who == game.actions[-1]['who'], rule_description="Players cannot play two times consecutively")
        gm.action_is_violation_if(lambda who, where, what, game: where != FREE_LABEL, "board", rule_description="The space needs to be free to put a sign on it.")
        gm.action_is_violation_if(lambda who, where, what, game: game.agents[who][1] != what, rule_description="Agents can only put their own sign.")

        return gm
    
    def act(self, action) -> None:
        player = action['who']
        coordinates = action['where']

        if player == 0:
            sign = 'X'
        elif player == 1:
            sign = 'O'
        else:
            raise ValueError("Player variable has to be 0 or 1")

        performed = self.model.action("board", player, coordinates, sign)

    """Trying out interactive jupyter""" 
    def __init__(self, explainer):
        super().__init__() 
    """  
    def __init__(self, explainer):
        super().__init__()
        self.explainer = explainer
        self.board_buttons = [[widgets.Button(description='', layout=widgets.Layout(width='50px', height='50px'))
                               for _ in range(3)] for _ in range(3)]
        self.explanation_output = widgets.Output()
        self.explain_button = widgets.Button(description="Explain Opponent's Move")
        self.explain_button.on_click(self.explain_opponent_move)
        self.jupyter_current_player = None
        self.player_dropdown = widgets.Dropdown(options=[], description="Current Player:")
        self.player_dropdown.observe(self.update_current_player, names='value')
        self.current_player = None
    
    def display_interface(self):
        self.player_dropdown.options = [(f"Player {i+1} ({self.players[i].__class__.__name__})", i) for i in self.players]
        board = widgets.GridBox(children=[self.board_buttons[i][j] for i in range(3) for j in range(3)],
                                layout=widgets.Layout(grid_template_columns='repeat(3, 50px)'))
        for i in range(3):
            for j in range(3):
                self.board_buttons[i][j].on_click(lambda _, x=i, y=j: asyncio.ensure_future(self.handle_click(x, y)))
        
        display(widgets.VBox([self.player_dropdown, board, self.explain_button, self.explanation_output]))
        
    def update_display_jupyter(self, state):
        for x in range(3):
            for y in range(3):
                value = state[x, y]
                self.board_buttons[x][y].description = value
                self.board_buttons[x][y].disabled = (value != FREE_LABEL)
    
    def update_current_player(self, change):
        self.jupyter_current_player = change['new']

    async def handle_click(self, x, y):
        if self.jupyter_current_player is not None:
            action = {'who': self.jupyter_current_player, 'where': (x, y), 'what': 'X' if self.jupyter_current_player == 0 else 'O'}
            await asyncio.to_thread(self.act, action)
            self.clear_console()
            current_state = self.tree.get_current_state().state
            self.update_display(current_state)
    
    def explain_opponent_move(self, _):
        with self.explanation_output:
            self.explanation_output.clear_output()
            explanation = self.explainer.explain_adjective(self.current_player.choice, 'the best', explanation_depth=4, with_framework='highlevel')
            print(explanation)
    
    def clear_jupyter(self):
        self.display_interface()
    """


def simple_scoring_function(node):
    """ Evaluate the Tic Tac Toe board state for the 'X' player's perspective """
    state = node.state
    score = 0
    
    # Possible lines to check (3 rows, 3 columns, 2 diagonals)
    lines = []
    # Rows and columns
    for i in range(3):
        lines.append(state[i, :])  # Row
        lines.append(state[:, i])  # Column
    # Diagonals
    lines.append(np.array([state[i, i] for i in range(3)]))  # Main diagonal
    lines.append(np.array([state[i, 2 - i] for i in range(3)]))  # Anti-diagonal

    for line in lines:
        if np.all(line == "X"):
            score += 100  # 'X' wins
        elif np.all(line == "O"):
            score -= 100  # 'O' wins
        elif np.count_nonzero(line == "X") == 2 and np.count_nonzero(line == "free") == 1:
            score += 10  # 'X' is one move away from winning
        elif np.count_nonzero(line == "O") == 2 and np.count_nonzero(line == "free") == 1:
            score -= 10  # 'O' is one move away from winning

    return score