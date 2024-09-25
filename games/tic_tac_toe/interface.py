from typing import Dict
import ipywidgets as widgets
from IPython.display import display
import asyncio

from src.game.interface import GameInterface
from src.game.game import User

class TicTacToeJupyterInterface(GameInterface):
    """
    Interface for the Tic Tac Toe game in Jupyter notebooks.

    This class handles the game's user interface, including the board display,
    player interactions, and game flow. It provides methods to create and update
    the game board, handle user inputs, and display game status.

    :param game: The TicTacToe game instance
    :type game: TicTacToe
    """

    def __init__(self, game):
        """
        Initialize the TicTacToeJupyterInterface.

        Sets up the game instance, buttons for the board, status label, and output area.
        Checks if the game instance has the required methods for the interface.

        :param game: The TicTacToe game instance
        :type game: TicTacToe
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' method
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

        Creates the board widget and displays it in the Jupyter notebook.
        This method should be called to initiate the game UI.
        """
        board_widget = self.create_board_widget()
        display(board_widget)

    def create_board_widget(self) -> widgets.VBox:
        """
        Create the board widget for the Jupyter notebook interface.

        Generates a 3x3 grid of buttons representing the Tic Tac Toe board,
        along with a status label and an output area for game messages.

        :return: A vertical box containing the game board, status label, and output area
        :rtype: widgets.VBox
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

        Generates a function that handles the click event for a specific button
        on the game board. When clicked, it processes the move if it's a user's turn.

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
    
    def update(self) -> None:
        """
        Update the game state in the interface.

        Refreshes the board display to reflect the current game state,
        updates button descriptions, and changes the status label based on
        whether the game has ended or it's the next player's turn.
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

        Sets the status label to display the game result, either declaring
        the winner or announcing a draw.
        """
        winner = self.game.winner()
        if winner is None:
            self.status_label.value = "Game Over! It's a draw!"
        else:
            self.status_label.value = f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"

    def update_next_player_status(self) -> None:
        """
        Update the status label for the next player's turn.

        Changes the status label to indicate which player (X or O) should make
        the next move.
        """
        next_player = 'X' if self.game.get_current_player().id == 0 else 'O'
        self.status_label.value = f"Player {next_player}'s turn"

    def clear_board_output(self) -> None:
        """
        Clear the board output in the Jupyter notebook interface.

        Removes any existing text from the output area below the game board.
        """
        if self.board_output:
            self.board_output.clear_output()
    
    def output(self, text: str) -> None:
        """
        Update the board output in the Jupyter notebook interface.

        Clears the existing output and displays new text in the output area
        below the game board.

        :param text: The text to display in the output area
        :type text: str
        """
        self.clear_board_output()
        with self.board_output:
            print(text)

import gradio as gr

class TicTacToeGradioInterface(GameInterface):
    """
    Interface for the Tic Tac Toe game using Gradio.

    This class handles the game's user interface, including the board display,
    player interactions, and game flow. It provides methods to create and update
    the game board, handle user inputs, and display game status.

    :param game: The TicTacToe game instance
    :type game: TicTacToe
    """

    def __init__(self, game):
        """
        Initialize the TicTacToeGradioInterface.

        Sets up the game instance and initializes Gradio components.

        :param game: The TicTacToe game instance
        :type game: TicTacToe
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' method
        """
        super().__init__(game)
        if not hasattr(self.game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the Gradio interface.")
        
        self.board = None
        self.status_label = None
        self.output_text = None
        self.coordinates_input = None

    def start(self):
        """
        Start the game interface.

        Creates the Gradio interface and launches it.
        """
        with gr.Blocks() as demo:
            gr.Markdown("# Tic Tac Toe")
            
            self.turn = gr.Textbox("X", interactive=False, label="Turn")
            self.board = gr.HTML(self.get_board_html())
            self.status_label = gr.Label("Player X's turn")
            self.output_text = gr.Textbox(label="Game Output", interactive=False)
            self.coordinates_input = gr.Textbox(label="Enter coordinates (row,col)", placeholder="e.g. 0,1")

            self.coordinates_input.submit(self.handle_move, inputs=[self.coordinates_input], outputs=[self.board, self.turn, self.status_label, self.output_text])

        demo.launch()

    def get_board_html(self):
        """
        Generate HTML for the Tic Tac Toe board.

        :return: HTML string representing the current board state
        """
        board_state = self.game.model.action_spaces["board"]
        html = "<table style='border-collapse: collapse; font-size: 24px;'>"
        for i in range(3):
            html += "<tr>"
            for j in range(3):
                cell_value = board_state[i, j] if board_state[i, j] != "" else "&nbsp;"
                html += f"<td style='width: 50px; height: 50px; text-align: center; vertical-align: middle; border: 1px solid black;'>{cell_value}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    def handle_move(self, coordinates):
        """
        Handle moves based on input coordinates.

        :param coordinates: String containing row and column, e.g. "0,1"
        :return: Updated values for board, turn, status label, and output text
        """
        if self.game.ended:
            return self.get_board_html(), self.turn.value, self.status_label.value, "Game has ended."

        try:
            i, j = map(int, coordinates.split(','))
            if not (0 <= i < 3 and 0 <= j < 3):
                raise ValueError("Coordinates out of range")
        except ValueError:
            return self.get_board_html(), self.turn.value, self.status_label.value, "Invalid coordinates. Use format: row,col (e.g. 0,1)"

        current_player = self.game.get_current_player()
        sign = self.game.model.agents[current_player.id, 1]

        if isinstance(current_player, User):
            if self.game.model.action_spaces["board"][i, j] == "":
                action = {'who': current_player.id, 'where': (i, j), 'what': sign, 'action_space': "board"}
                self.game.act(action)
                asyncio.create_task(self.game.continue_game())
            else:
                return self.get_board_html(), self.turn.value, self.status_label.value, "This cell is already occupied."

        return self.get_updated_values()

    def update(self):
        """
        Update the game state in the interface.

        Refreshes the board display to reflect the current game state,
        updates the turn indicator, and changes the status label based on
        whether the game has ended or it's the next player's turn.
        """
        self.board.value = self.get_board_html()

        current_player = self.game.get_current_player()
        self.turn.value = self.game.model.agents[current_player.id, 1]

        if self.game.ended:
            self.update_end_game_status()
        else:
            self.update_next_player_status()

    def update_end_game_status(self):
        """
        Update the status label for game end scenarios.

        Sets the status label to display the game result, either declaring
        the winner or announcing a draw.
        """
        winner = self.game.winner()
        if winner is None:
            self.status_label.value = "Game Over! It's a draw!"
        else:
            self.winner_sign = self.game.model.agents[winner, 1]
            self.status_label.value = f"Game Over! Player {self.winner_sign} wins!"

    def update_next_player_status(self):
        """
        Update the status label for the next player's turn.

        Changes the status label to indicate which player (X or O) should make
        the next move.
        """
        next_player = self.game.model.agents[self.game.get_current_player().id, 1]
        self.status_label.value = f"Player {next_player}'s turn"

    def output(self, text: str):
        """
        Update the output text in the Gradio interface.

        :param text: The text to display in the output area
        :type text: str
        """
        self.output_text.value = text

    def get_updated_values(self):
        """
        Get the current values of all interface components.

        :return: List of current values for board, turn, status label, and output text
        """
        return [self.get_board_html(), self.turn.value, self.status_label.value, self.output_text.value]