from typing import Dict
import ipywidgets as widgets
from IPython.display import display
import asyncio

from src.game.game import User

class TicTacToeJupyterInterface:
    """
    Interface for the Tic Tac Toe game.

    This class handles the game's user interface, including the board display,
    player interactions, and game flow.

    :param game: The TicTacToe game instance
    :type game: TicTacToe
    """

    def __init__(self, game):
        """
        Initialize the TicTacToeInterface.

        :param game: The TicTacToe game instance
        :type game: TicTacToe
        """
        self.game = game
        if not hasattr(self.game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the jupyter interface.")
        
        self.buttons: Dict[tuple, widgets.Button] = {}
        self.status_label: widgets.Label = None
        self.board_output: widgets.Output = None

    def start(self) -> None:
        """
        Start the game interface.
        """
        board_widget = self.create_board_widget()
        display(board_widget)

    def create_board_widget(self) -> widgets.VBox:
        """
        Create the board widget for the Jupyter notebook interface.

        :return: The created board widget
        :rtype: ipywidgets.VBox
        """
        for i in range(3):
            for j in range(3):
                button = widgets.Button(
                    description='', 
                    layout=widgets.Layout(
                        width='50px', 
                        height='50px', 
                        margin='0px',
                        border='1px solid black'
                    )
                )
                button.on_click(self.create_button_click_handler(i, j))
                self.buttons[(i, j)] = button

        self.status_label = widgets.Label(value="Player X's turn")
        self.board_output = widgets.Output()
        
        board_widget = widgets.GridBox(
            children=list(self.buttons.values()),
            layout=widgets.Layout(
                grid_template_columns="repeat(3, auto)",
                grid_gap='0px',
                width='150px',
                height='150px'
            )
        )
        return widgets.VBox([board_widget, self.status_label, self.board_output])

    def create_button_click_handler(self, i: int, j: int):
        """
        Create a click handler for a board button.

        :param i: Row index of the button
        :type i: int
        :param j: Column index of the button
        :type j: int
        :return: The click handler function
        :rtype: function
        """
        def handle_click(b):
            current_player = self.game.get_current_player()
            sign = self.game.model.agents[current_player.id, 1]
            
            if isinstance(current_player, User):
                action = {'who': current_player.id, 'where': (i, j), 'what': sign, 'action_space': "board"}
                self.game.act(action)
                asyncio.create_task(self.game.continue_game())
        return handle_click
    
    def update_game_state(self) -> None:
        """
        Update the game state, including the board display and status label.
        """
        # Update board buttons
        board_state = self.game.model.action_spaces["board"]
        for (i, j), button in self.buttons.items():
            button.description = board_state[i, j]

        # Update status label
        if self.game.ended:
            self.update_end_game_status()
        else:
            self.update_next_player_status()

    def update_end_game_status(self) -> None:
        """
        Update the status label for game end scenarios.
        """
        winner = self.game.winner()
        if winner is None:
            self.status_label.value = "Game Over! It's a draw!"
        else:
            self.status_label.value = f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"

    def update_next_player_status(self) -> None:
        """
        Update the status label for the next player's turn.
        """
        next_player = 'X' if self.game.get_current_player().id == 0 else 'O'
        self.status_label.value = f"Player {next_player}'s turn"

    def clear_board_output(self) -> None:
        """
        Clear the board output in the Jupyter notebook interface.
        """
        if self.board_output:
            self.board_output.clear_output()
    
    def update_board_output(self, text: str) -> None:
        """
        Update the board output in the Jupyter notebook interface.

        :param text: The text to display
        :type text: str
        """
        self.clear_board_output()
        with self.board_output:
            print(text)