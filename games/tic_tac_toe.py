from typing import Dict

import numpy as np

from src.game.game import Game, GameModel, GameTree, User

import ipywidgets as widgets
from IPython.display import display, HTML
import asyncio
from functools import wraps

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
    
    def _act(self, action) -> None:
        player = action['who']
        coordinates = action['where']

        if player == 0:
            sign = 'X'
        elif player == 1:
            sign = 'O'
        else:
            raise ValueError("Player variable has to be 0 or 1")

        return "board", player, coordinates, sign

    """Interactive game handling"""
    def __init__(self):
        super().__init__()
        self.buttons = None
        self.status_label = None
        self.board_output = None
    
    def get_current_player_id(self):
        if not self.started:
            return next(id for id, player in self.players.items() if self.model.agents[id, 0] == 'starter')
        else:
            last_player = self.model.actions[-1]['who']
            return next(id for id in self.players.keys() if id != last_player)

    def create_board_widget(self):
        self.buttons = [[widgets.Button(
            description='', 
            layout=widgets.Layout(
                width='50px', 
                height='50px', 
                margin='0px',
                border='1px solid black'
            )
        ) for _ in range(3)] for _ in range(3)]
        self.status_label = widgets.Label(value="Player X's turn")
        self.board_output = widgets.Output()
        
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].on_click(self.create_button_click_handler(i, j))
        
        board_widget = widgets.GridBox(
            children=[button for row in self.buttons for button in row],
            layout=widgets.Layout(
                grid_template_columns="repeat(3, auto)",
                grid_gap='0px',
                width='150px',
                height='150px'
            )
        )
        return widgets.VBox([board_widget, self.status_label, self.board_output])

    def clear_board_output(self):
        if self.board_output:
            self.board_output.clear_output()

    def create_button_click_handler(self, i, j):
        def handle_click(b):
            current_player_id = self.get_current_player_id()
            current_player = self.players[current_player_id]
            sign = self.model.agents[current_player_id, 1]  # Get the correct sign from the game model
            
            if isinstance(current_player, User):
                action = {'who': current_player_id, 'where': (i, j), 'what': sign, 'action_space': "board"}
                self.act(action)
                asyncio.create_task(self.continue_game())
        return handle_click

    def update_board(self):
        board_state = self.model.action_spaces["board"]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].description = board_state[i, j] if board_state[i, j] != FREE_LABEL else ''

        if self.ended:
            winner = self.model.actions[-1]['who']
            if np.all(self.model.action_spaces["board"] != FREE_LABEL):
                self.status_label.value = "Game Over! It's a draw!"
            else:
                self.status_label.value = f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"
        else:
            next_player = 'X' if self.get_current_player_id() == 0 else 'O'
            self.status_label.value = f"Player {next_player}'s turn"

    async def turn_handler(self):
        self.clear_board_output()
        current_player_id = self.get_current_player_id()
        current_player = self.players[current_player_id]
        sign = self.model.agents[current_player_id, 1]

        if not isinstance(current_player, User):
            with self.board_output:
                print(f"AI player {sign} is thinking...")
            await current_player.play(self)
            await self.continue_game()
        else:
            with self.board_output:
                print(f"User player {sign} is thinking...")

        self.update_board()

    async def continue_game(self):
        self.update_board()
        if not self.ended:
            await self.turn_handler()

    async def start_on_jupyter(self):
        board_widget = self.create_board_widget()
        self.update_board()
        display(board_widget)
        await self.turn_handler()

def simple_scoring_function(node, depth):
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

def simple_depth_dependant_scoring_function(node, depth):
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
            score += 1000 + depth # 'X' wins
        elif np.all(line == "O"):
            score -= 1000 - depth # 'O' wins
        elif np.count_nonzero(line == "X") == 2 and np.count_nonzero(line == "free") == 1:
            score += 100 + depth # 'X' is one move away from winning
        elif np.count_nonzero(line == "O") == 2 and np.count_nonzero(line == "free") == 1:
            score -= 100 - depth  # 'O' is one move away from winning

    return score