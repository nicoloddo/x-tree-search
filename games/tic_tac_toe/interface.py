from typing import Dict
import ipywidgets as widgets
from IPython.display import display
import asyncio
import traceback
import os

from src.game.interface import GameInterface
from src.game.agents import User

import gradio as gr
from src.explainer.interface.gradio_interface import ExplainerGradioInterface

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


class TicTacToeGradioInterface(GameInterface):

    """
    Interface for the Tic Tac Toe game using Gradio.

    This class handles the game's user interface, including the board display,
    player interactions, game flow, and AI move explanations. It provides methods to create and update
    the game board, handle user inputs, display game status, and explain AI moves.
    """
    assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    empty_cell_name = "cell"

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
        
        self.board_images = None
        self.gallery_settings = None
        self.status = None
        self.output_text = None
        self.ai_explanation = None
        self.skip_score_statement = True
        self.explainer = game.explainer
        self.explainer_interface = ExplainerGradioInterface(game=self.game, explanation_depth=3)

    def start(self, share_gradio=False):
        """
        Start the game interface.

        Initializes the game state and launches the Gradio interface.
        """
        self.started = True
        
        with gr.Blocks(css="""
            .grid-container {
                grid-column-gap: 0px; 
                grid-row-gap: 0px; 
                overflow: hidden;
            }
        """) as iface:
            with gr.Tab("Game"):
                gr.Markdown("# Tic Tac Toe")
                with gr.Row(equal_height=True):
                    with gr.Column():
                        self.status = gr.Textbox(label="Status", value=self.status)
                        self.output_text = gr.Textbox(label="Output", value=self.output_text)
                
                    with gr.Column():
                        self.gallery_settings = {
                            "columns": 3,
                            "rows": 3,
                            "height": "max-content",
                            "allow_preview": False,
                            "show_label": False,
                            "elem_id": "board"
                        }
                        self.update_board()

            # Build explainer tabs
            ai_explanation_components = self.explainer_interface.build_ai_explanation_tab(tab_label="Explain", toggles={"skip_score_toggle": ("Skip Score Statement", True)})
            visualize_components = self.explainer_interface.build_visualize_tab(tab_label="Visualize Explanation Framework")
            self.explainer_interface.connect_components({**visualize_components, **ai_explanation_components})

            self.board_images.select(
                self.process_move,
                inputs=[],
                outputs=[self.board_images, self.status, self.output_text, ai_explanation_components["explanation_output"]]
            )

            skip_score_toggle = ai_explanation_components["skip_score_toggle"]
            skip_score_toggle.change(
                self.toggle_skip_score,
                inputs=[skip_score_toggle],
                outputs=[ai_explanation_components["explanation_output"]]
            )
        
        # Put the update outside of the Blocks to make sure the board is not displayed two times
        self.update()
        iface.launch(share=share_gradio)

    def update(self):
        """
        Update the game state in the interface.

        Refreshes the board display, status, and output based on the current game state.
        This method can be called from outside classes to update the interface.
        """
        self.update_board()

        opponent = next((player for player in self.game.players.values() if not isinstance(player, User)), None)
        self.ai_explanation = self.explainer_interface.update_ai_explanation(opponent)

        if self.game.ended:
            self.update_end_game_status()
        else:
            self.update_next_player_status()

    def update_board(self):
        """
        Update the board images based on the current game state.
        """
        board_state = self.game.model.action_spaces["board"]
        updated_images = []
        for i in range(3):
            for j in range(3):
                cell_value = board_state[i, j]
                image_name = self.empty_cell_name
                if cell_value == 'X':
                    image_name += '_x'
                elif cell_value == 'O':
                    image_name += '_o'
                updated_images.append(f"{self.assets_folder}/{image_name}.jpg")

        self.board_images = gr.Gallery(
            value=updated_images,
            **self.gallery_settings
        )

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
        opponent = next((player for player in self.game.players.values() if not isinstance(player, User)), None)
        self.ai_explanation = self.explainer_interface.update_ai_explanation(opponent)
        
        return self.ai_explanation

    async def process_move(self, evt: gr.SelectData):
        """
        Process a move made by the current player.

        :param evt: The event data containing the selected index
        :type evt: gr.SelectData
        :return: Updated board images, status, output text, and AI explanation
        :rtype: Tuple[gr.Gallery, str, str, str]
        """
        try:
            index = evt.index
            row, col = index // 3, index % 3
            current_player = self.game.get_current_player()
            sign = self.game.model.agents[current_player.id, 1]
            inputs = {'what': sign, 'where': (row, col), 'action_space': "board"}
            await current_player.play(self.game, inputs)
        except Exception as e:
            self.output(str(e))
            print(f"Detailed error: {type(e).__name__}: {str(e)}")  # For debugging
            print("Full traceback:")
            traceback.print_exc()

        self.update()
        return self.board_images, self.status, self.output_text, self.ai_explanation


if __name__ == "__main__":
    from games.tic_tac_toe.tic_tac_toe import TicTacToe
    from explainers.alphabeta_explainer import AlphaBetaExplainer
    explainer = AlphaBetaExplainer()
    game = TicTacToe(explainer=explainer)
    user1 = User(agent_id=0)
    user2 = User(agent_id=1)
    game.set_players([user1, user2])

    # Run the game start in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(game.start_game(share_gradio=False))
    loop.close()
