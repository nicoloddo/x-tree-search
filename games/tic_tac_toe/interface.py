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

from PIL import Image, ImageDraw, ImageFont

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

    def __init__(self, game, interface_hyperlink_mode=True):
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
        
        self.board_gallery = None
        self.cell_images = self.create_cell_images()
        self.showing_state = None
        self.gallery_settings = None
        self.status = None
        self.output_text = None
        self.ai_explanation = None
        self.ai_explanation_components = None
        self.skip_score_statement = True
        self.explainer = game.explainer

        self.explaining_agent = next((player for player in self.game.players.values() if not isinstance(player, User)), None)
        self.explainer_interface = ExplainerGradioInterface(game=self.game, explanation_depth=3, explaining_agent=self.explaining_agent, explain_in_hyperlink_mode=interface_hyperlink_mode)

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
        """, fill_width=True) as demo:
            with gr.Tabs() as tabs:
                with gr.TabItem("Game", id=self.explainer_interface.tab_ids["other"] + 0):
                    with gr.Row(equal_height=False):
                        with gr.Column(scale=1):
                            gr.Markdown("# Tic Tac Toe")
                            with gr.Row():
                                self.status = gr.Textbox(label="Status", value=self.status, scale=1)
                                self.showing_state = gr.Textbox(label="Showing", value=self.showing_state, scale=1)
                            with gr.Row():
                                restart_button = gr.Button("Restart Game", scale=1)
                                show_current_button = gr.Button("Show Current State", scale=1)

                            info = """Click on a move in the explanation to see it on the board.\nClick on the Show Current State button to go back to the game."""
                            gr.HTML(ExplainerGradioInterface.cool_html_text_container.format(info))

                            self.gallery_settings = {
                                "columns": 3,
                                "rows": 3,
                                "height": "max-content",
                                "allow_preview": False,
                                "show_label": False,
                                "elem_id": "board"
                            }
                            self.board_gallery = gr.Gallery(
                                value=[],
                                **self.gallery_settings
                            )
                            self.output_text = gr.Textbox(label="Output", value=self.output_text)
                    
                        with gr.Column(scale=2):
                            gr.Markdown("# AI Move Explanation")
                            self.ai_explanation_components = self.explainer_interface.interface_builder.build_ai_explanation_components(
                                toggles={"skip_score_toggle": ("Skip Score Statement (the explainer is designed around skipping the score statement, problems may arise when this is disabled)", True)})

                with gr.TabItem("Visualize", self.explainer_interface.tab_ids["visualize"]):
                    visualize_components = self.explainer_interface.interface_builder.build_visualize_components()

            # Handle components connections   
            self.explainer_interface.interface_builder.connect_components({**self.ai_explanation_components, **visualize_components})

            all_available_outputs = [self.board_gallery, self.showing_state, 
                                     self.status, self.output_text, 
                                     self.ai_explanation_components["explanation_output"], 
                                     self.ai_explanation_components["id_input"],
                                     self.ai_explanation_components["explaining_question"]]

            self.board_gallery.select(
                self.process_move,
                inputs=[],
                outputs=all_available_outputs
            )

            show_current_button.click(
                self.get_updated_board_gallery,
                inputs=[],
                outputs=[self.board_gallery, self.showing_state, self.ai_explanation_components["id_input"]]
            )

            restart_button.click(
                self.restart_game,
                inputs=[],
                outputs=all_available_outputs
            )

            skip_score_toggle = self.ai_explanation_components["skip_score_toggle"]
            skip_score_toggle.change(
                self.toggle_skip_score,
                inputs=[skip_score_toggle],
                outputs=all_available_outputs
            )

            # Initial update
            demo.load(
                self.on_load,
                inputs=[],
                outputs=all_available_outputs,
            )
        
        demo.launch(share=share_gradio)

    def restart_game(self):
        """
        Restart the game.
        """
        self.game.restart()
        return self.update()

    def on_load(self, request: gr.Request):
        """
        On load event handler.
        """
        self.explainer_interface.on_load(request)

        show_node_id = None
        explain_node_id = None
        explain_adjective = None
        if request:
            query_params = dict(request.query_params)
            if 'show_node_id' in query_params:
                show_node_id = query_params['show_node_id']
                explain_node_id = query_params['node_id']
                explain_adjective = query_params['adjective']

        return self.update(explain_node_id=explain_node_id, explain_adjective=explain_adjective, show_node_id=show_node_id)

    def update(self, explain_node_id=None, explain_adjective=None, show_node_id=None):
        """
        Update the game state in the interface.

        Refreshes the board display, status, and output based on the current game state.
        Consider that due to Gradio's event handling approach, this method will not do anything when
        called directly, but it rather need to be attached to an event to be applied correctly.

        :return: Updated board images, status, output text, and AI explanation
        :rtype: Tuple[List[str], str, str, str]
        """
        board_gallery, showing_state, show_node_id = self.get_updated_board_gallery(show_node_id)
        status = self.get_updated_status()
        output_text = self.output_text  # Update in case the self.output_text was changed
        ai_explanation = self.ai_explanation_components["explanation_output"].value
        explaining_question = self.ai_explanation_components["explaining_question"].value

        adjective = explain_adjective or "the best"
        ai_explanation, explaining_question = self.explainer_interface.ai_explainer.update_ai_explanation(explain_node_id, adjective)

        return board_gallery, showing_state, status, output_text, ai_explanation, show_node_id, explaining_question

    def get_updated_board_gallery(self, node_id=None):
        """
        Get the updated board images based on the current game state.

        :param node_id: The ID of the node to explain
        :type node_id: str
        :return: The updated board gallery, showing state, and node ID
        :rtype: Tuple[gr.Gallery, str, str]
        """
        # Determine the node to display and its corresponding board state
        if node_id is None:
            # If no specific node is requested, use the current choice of the explaining agent
            node_id = self.explaining_agent.choice.id if self.explaining_agent.choice else ""
            board_state = self.game.model.action_spaces["board"]
            showing_state = f"Current State ({node_id})" if node_id else "Current State"
            parent_state = None
        else:
            # If a specific node is requested, fetch it from the explaining agent's core
            node = self.explaining_agent.core.nodes[node_id]
            parent_state = node.parent_state
            current_id = self.explaining_agent.choice.id

            # Determine if the requested node is the current state or a different node
            if current_id == node_id:
                board_state = self.game.model.action_spaces["board"]
                showing_state = f"Current State ({node_id})"
            else:
                board_state = node.game_state
                showing_state = f"Node {node_id}"

        updated_images = []
        for i in range(3):
            for j in range(3):
                cell_value = board_state[i, j]
                is_changed = parent_state is not None and parent_state[i, j] != cell_value
                cell_image = self.get_cell_image(cell_value, is_changed, i, j)
                updated_images.append(cell_image)
        
        board_gallery = gr.Gallery(
            value=updated_images,
            **self.gallery_settings
        )
        return board_gallery, showing_state, node_id
    
    def get_cell_image(self, cell_value, is_changed, i, j):
        """
        Get the appropriate cell image and add the index.
        """
        if cell_value == '' or cell_value == ' ':
            img = self.cell_images['empty'].copy()
        else:
            img_key = f"{cell_value}_red" if is_changed else cell_value
            img = self.cell_images[img_key].copy()
        
        # Add index to the image
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default().font_variant(size=15)
        draw.text((5, 3), f"{i},{j}", font=font, fill='blue')
        
        return img
    
    def create_cell_images(self):
        """
        Create and store all possible cell images.
        """
        cell_size = 100
        images = {}
        for cell_type in ['empty', 'X', 'O', 'X_red', 'O_red']:
            img = Image.new('RGB', (cell_size, cell_size), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw border
            draw.rectangle([0, 0, cell_size-1, cell_size-1], outline='black', width=2)
            
            if cell_type != 'empty':
                font = ImageFont.load_default().font_variant(size=80)
                text = cell_type[0]  # 'X' or 'O'
                text_color = 'red' if cell_type.endswith('_red') else 'black'
                
                left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                text_width = right - left
                text_height = bottom - top
                position = ((cell_size - text_width) / 2, (cell_size - text_height*1.7) / 2)
                draw.text(position, text, font=font, fill=text_color)
            
            images[cell_type] = img
        return images

    def get_updated_status(self):
        """
        Get the updated status based on the current game state.

        :return: Updated status text
        :rtype: str
        """
        if self.game.ended:
            winner = self.game.winner()
            if winner is None:
                return "Game Over! It's a draw!"
            else:
                return f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"
        else:
            next_player = 'X' if self.game.get_current_player().id == 0 else 'O'
            return f"Player {next_player}'s turn"

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
        
        return self.update()

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

        return self.update()


if __name__ == "__main__":
    # Test Gradio Interface
    from games.tic_tac_toe.tic_tac_toe import TicTacToe
    from explainers.alphabeta_explainer import AlphaBetaExplainer
    explainer = AlphaBetaExplainer()
    user1 = User(agent_id=0)
    user2 = User(agent_id=1)

    game = TicTacToe(explainer=explainer, players=[user1, user2])

    # Run the game start in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(game.start_game(share_gradio=False))
    loop.close()
