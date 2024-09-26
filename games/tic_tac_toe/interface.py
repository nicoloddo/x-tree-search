from typing import Dict
import ipywidgets as widgets
from IPython.display import display
import asyncio

from src.game.interface import GameInterface
from src.game.agents import User

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
        super().__init__(game)
        if not hasattr(self.game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the jupyter interface.")
        
        self.buttons: Dict[tuple, widgets.Button] = {}
        self.status_label: widgets.Label = None
        self.board_output: widgets.Output = None
        self.board_widget: widgets.VBox = None

    def start(self) -> None:
        """
        Start the game interface.

        Creates the board widget and displays it in the Jupyter notebook.
        This method should be called to initiate the game UI.
        """
        self.started = True
        self.board_widget = self.create_board_widget()
        display(self.board_widget)
        self.update()

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

    def create_button_click_handler(self, row: int, col: int):
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
            try:
                current_player = self.game.get_current_player()
                sign = self.game.model.agents[current_player.id, 1]
                inputs = {'what': sign, 'where': (row, col), 'action_space': "board"}
                asyncio.create_task(current_player.play(self.game, inputs))

            except Exception as e:
                self.output(str(e))

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
    player interactions, game flow, and AI move explanations. It provides methods to create and update
    the game board, handle user inputs, display game status, and explain AI moves.
    """

    def __init__(self, game):
        """
        Initialize the TicTacToeGradioInterface.

        Sets up the game instance and initializes necessary attributes.

        :param game: The TicTacToe game instance
        :type game: TicTacToe
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' method
        """
        super().__init__(game)
        if not hasattr(self.game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the Gradio interface.")
        
        self.board_html = None
        self.status = None
        self.output_text = None
        self.ai_explanation = None
        self.skip_score_statement = True
        self.explainer = game.explainer

    def start(self, share_gradio=False):
        """
        Start the game interface.

        Initializes the game state and launches the Gradio interface.
        """
        self.started = True
        self.update()
        with gr.Blocks() as iface:
            with gr.Tab("Game"):
                gr.Markdown("# Tic Tac Toe")
                move_input = gr.Textbox(label="Enter move (row,col)")
                board_output = gr.HTML(label="Board", value=self.board_html)
                status_output = gr.Textbox(label="Status", value=self.status)
                game_output = gr.Textbox(label="Output", value=self.output_text)
                move_button = gr.Button("Make Move")
            
            with gr.Tab("Explain"):
                gr.Markdown("# AI Move Explanation")
                explanation_output = gr.Markdown(value=self.ai_explanation, label="AI move explanation")
                skip_score_toggle = gr.Checkbox(label="Skip Score Statement", value=True)
            
            move_button.click(
                self.process_move,
                inputs=[move_input],
                outputs=[board_output, status_output, game_output, explanation_output]
            )
            
            skip_score_toggle.change(
                self.toggle_skip_score,
                inputs=[skip_score_toggle],
                outputs=[explanation_output]
            )

        iface.launch(share=share_gradio)

    def update(self):
        """
        Update the game state in the interface.

        Refreshes the board display, status, and output based on the current game state.
        This method can be called from outside classes to update the interface.
        """
        self.update_board()
        self.update_ai_explanation()
        if self.game.ended:
            self.update_end_game_status()
        else:
            self.update_next_player_status()

    def update_board(self):
        """
        Update the HTML representation of the game board.
        """
        board_state = self.game.model.action_spaces["board"]
        html = "<table style='border-collapse: collapse; font-size: 24px;'>"
        for i in range(3):
            html += "<tr>"
            for j in range(3):
                cell_value = board_state[i, j]
                html += f"<td style='width: 50px; height: 50px; text-align: center; vertical-align: middle; border: 1px solid white;'>{cell_value}</td>"
            html += "</tr>"
        html += "</table>"
        self.board_html = html

    def update_end_game_status(self):
        """
        Update the status for game end scenarios.
        """
        winner = self.game.winner()
        if winner is None:
            self.status = "Game Over! It's a draw!"
        else:
            self.status = f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"

    def update_next_player_status(self):
        """
        Update the status for the next player's turn.
        """
        next_player = 'X' if self.game.get_current_player().id == 0 else 'O'
        self.status = f"Player {next_player}'s turn"

    def update_ai_explanation(self):
        """
        Update the AI explanation.
        """
        opponent = next((player for player in self.game.players.values() if not isinstance(player, User)), None)
        if opponent:
            self.ai_explanation = self.game.explainer.explain(opponent.choice, 'the best')

    def output(self, text: str):
        """
        Update the output text.

        :param text: The text to display in the output area
        :type text: str
        """
        self.output_text = text

    def toggle_skip_score(self, skip_score: bool):
        """
        Toggle the skip score statement setting and update the explanation.

        :param skip_score: Whether to skip the score statement or not
        :type skip_score: bool
        :return: Updated AI explanation
        :rtype: str
        """
        self.skip_score_statement = skip_score
        self.game.explainer.frameworks['highlevel'].get_adjective('score').skip_statement = skip_score
        
        # Update the explanation if there's a current AI move
        if self.ai_explanation:
            self.update_ai_explanation()
        
        return self.ai_explanation

    async def process_move(self, move_input: str):
        """
        Process a move input from the user and handle AI moves.

        :param move_input: The move input in the format "row,col"
        :type move_input: str
        :return: Updated board HTML, status, output, and AI explanation
        :rtype: tuple
        """
        try:
            row, col = map(int, move_input.split(','))
            current_player = self.game.get_current_player()
            sign = self.game.model.agents[current_player.id, 1]
            inputs = {'what': sign, 'where': (row, col), 'action_space': "board"}
            await current_player.play(self.game, inputs)

        except ValueError:
            self.output("Invalid input. Please enter row,col (e.g., 0,0)")
        except Exception as e:
            self.output(str(e))

        return self.board_html, self.status, self.output_text, self.ai_explanation
