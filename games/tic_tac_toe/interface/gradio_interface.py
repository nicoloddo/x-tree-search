from PIL import Image, ImageDraw, ImageFont
import traceback
import os
import asyncio

from src.game.agents import User
from src.game.interface import GameInterface

import gradio as gr
from src.explainer.interface.gradio_interface import ExplainerGradioInterface

class TicTacToeGradioInterface(GameInterface):

    """
    Interface for the Tic Tac Toe game using Gradio.

    This class handles the game's user interface, including the board display,
    player interactions, game flow, and AI move explanations. It provides methods to create and update
    the game board, handle user inputs, display game status, and explain AI moves.
    """
    assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    empty_cell_name = "cell"

    @classmethod
    def create_board_cell_images(cls):
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

    def __init__(self, game=None, explainer=None, interface_hyperlink_mode=True, *, create_game_method: callable = None):
        """
        Initialize the TicTacToeGradioInterface.

        Sets up the game instance and initializes necessary attributes.

        :param game: The TicTacToe game instance
        :type game: TicTacToe
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' or 'explaining_agent' attributes
        """
        super().__init__()
        self.board_gallery = None
        self.board_cell_images = TicTacToeGradioInterface.create_board_cell_images()
        self.showing_state = None
        self.gallery_settings = None
        self.status = None
        self.output_text = None
        self.ai_explanation = None
        self.ai_explanation_components = None
        self.skip_score_statement = True
        
        self.init_explainer = explainer
        self.explainer_interface = ExplainerGradioInterface(explainer=self.init_explainer, explain_in_hyperlink_mode=interface_hyperlink_mode)

        self.init_game = None
        if game is not None:
            if create_game_method is not None:
                raise SyntaxError("Do not provide an create_game_method method if you are already providing a game instance.")
            self.init_game = game
        elif create_game_method is not None:
            self.create_game_method = create_game_method
        else:
            raise SyntaxError("Either provide a game instance or a create_game_method method.")
        
    def create_interface(self):
        """
        Create the interface for the Tic Tac Toe game.
        """
        #************************
        # 1. Define the interface
        #
        with gr.Blocks(
            css="""
                .grid-container {
                    grid-column-gap: 0px; 
                    grid-row-gap: 0px; 
                    overflow: hidden;
                }
                """, # Perfectionates the board display
            fill_width=True) as demo:
            game_state = gr.State(self.create_game())
            explainer_state = gr.State(self.init_explainer)

            with gr.Tabs() as tabs:
                with gr.TabItem("Game and Explain", id=self.explainer_interface.tab_ids["other"] + 0):
                    with gr.Row(equal_height=False):
                        with gr.Column(scale=1):
                            gr.Markdown("# Tic Tac Toe (vs Alpha-Beta Pruning Minimax)")
                            with gr.Row():
                                self.status = gr.Textbox(label="Status", value=self.status, scale=1)
                                self.showing_state = gr.Textbox(label="Showing (drag and drop to change)", value=self.showing_state, scale=1, interactive=True)
                            with gr.Row():
                                self.restart_button = gr.Button("Restart Game", scale=1)
                                self.show_current_button = gr.Button("Return to Current State", scale=1)

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
                            self.output_text = gr.HTML("")
                    
                        with gr.Column(scale=2):
                            gr.Markdown("# AI Move Explanation")
                            self.ai_explanation_components = self.explainer_interface.interface_builder.build_ai_explanation_components(
                                game_state,
                                explainer_state,
                                toggles={"skip_score_toggle": ("Skip Score Statement (the explainer is designed around skipping the score statement, problems may arise when this is disabled)", True)},
                                additional_info="P.S. To visualize a move on the board you can drag and drop the move from the explanation to the \"Showing\" widget."
                            )

                with gr.TabItem("Visualize Decision Tree", self.explainer_interface.tab_ids["visualize_decision_tree"]):
                    self.visualize_decision_tree_components = self.explainer_interface.interface_builder.build_visualize_decision_tree_components(game_state)

                with gr.TabItem("Visualize Framework", self.explainer_interface.tab_ids["visualize"]):
                    self.visualize_components = self.explainer_interface.interface_builder.build_visualize_components()
                
                with gr.TabItem("Settings", self.explainer_interface.tab_ids["settings"]):
                    self.explainer_settings_components = self.explainer_interface.interface_builder.build_explainer_settings_components()
                    self.explainer_settings_fields = list(self.explainer_settings_components.values())[:-1] # exclude the apply button

            #*********************************
            # 2. Handle components connections 
            #
            self.explainer_interface.interface_builder.connect_components({**self.ai_explanation_components, **self.visualize_components, 
                                                                           **self.visualize_decision_tree_components, **self.explainer_settings_components}, 
                                                                           game_state, explainer_state)

            all_available_outputs = [game_state, self.board_gallery, self.showing_state, 
                                     self.status, self.output_text, 
                                     self.ai_explanation_components["explanation_output"], 
                                     self.ai_explanation_components["id_input"],
                                     self.ai_explanation_components["explain_adj_name"],
                                     self.ai_explanation_components["explaining_question"],
                                     self.ai_explanation_components["current_node_id"],
                                     self.ai_explanation_components["current_adjective"],
                                     self.ai_explanation_components["current_comparison_id"]]
            
            game_state.change(
                self.update,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs
            )

            self.showing_state.change(
                self.update_showing_state,
                inputs=[game_state, self.showing_state],
                outputs=[self.board_gallery, self.showing_state, self.ai_explanation_components["id_input"]]
            )

            self.board_gallery.select(
                self.process_move,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs
            )

            self.show_current_button.click(
                self.update_board_gallery,
                inputs=[game_state],
                outputs=[self.board_gallery, self.showing_state, self.ai_explanation_components["id_input"]]
            )

            self.restart_button.click(
                self.restart_game,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs
            )

            def toggle_skip_score(game, explainer, skip_score: bool, current_node_id: str, current_adjective: str, current_comparison_id: str, explanation_depth: int):
                """
                Toggle the skip score statement setting and update the explanation.
                """
                self.skip_score_statement = skip_score
                explainer.frameworks['highlevel'].get_adjective('score').skip_statement = skip_score

                ai_explanation, explaining_question, _, _, _ = self.explainer_interface.ai_explainer.update_ai_explanation(game, explainer, current_node_id, current_adjective, current_comparison_id, explanation_depth)
                
                return ai_explanation, explaining_question

            skip_score_toggle = self.ai_explanation_components["skip_score_toggle"]
            skip_score_toggle.change(
                toggle_skip_score,
                inputs=[game_state, explainer_state, skip_score_toggle, self.ai_explanation_components["current_node_id"], self.ai_explanation_components["current_adjective"], self.ai_explanation_components["current_comparison_id"], self.ai_explanation_components["explanation_depth"]],
                outputs=[self.ai_explanation_components["explanation_output"], self.ai_explanation_components["explaining_question"]]
            )

            # Initial update
            demo.load(
                self.on_load,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs,
            )

        return demo

    def start(self, share_gradio=False):
        """
        Start the game interface.

        Initializes the game state and launches the Gradio interface.
        """
        self.started = True
        demo = self.create_interface()
        demo.launch(share=share_gradio)

    def on_load(self, game, explainer, request: gr.Request):
        """
        On load event handler.
        """
        self.explainer_interface.on_load(request)

        return self.update(game, explainer)
    
    def output(self, text: str, type: str = "info"):
        """
        Handle output information.

        :param text: The text to display in the output area
        :type text: str
        """
        if len(text) == 0:
            return
        
        if type == "info":
            self.output_text = ExplainerGradioInterface.cool_html_text_container.format(text)
            gr.Info(text)
        elif type == "error":
            gr.Warning(text)
        elif type == "warning":
            gr.Warning(text)
        else:
            raise ValueError(f"Invalid type {type}")

    def update(self, game, explainer, show_node_id=None):
        """
        Update the game state in the interface.

        Refreshes the board display, status, and output based on the current game state.
        Consider that due to Gradio's event handling approach, this method will not do anything when
        called directly, but it rather need to be attached to an event to be applied correctly.

        :return: Updated board images, status, output text, and AI explanation
        :rtype: Tuple[List[str], str, str, str]
        """
        if game is None:
            return gr.Gallery(), "Start a Game to show the board", None, None, None, None, None, None
        
        def get_updated_status(game):
            """
            Get the updated status based on the current game state.

            :return: Updated status text
            :rtype: str
            """
            if game.ended:
                winner = game.winner()
                if winner is None:
                    return "Game Over! It's a draw!"
                else:
                    return f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"
            else:
                next_player = 'X' if game.get_current_player().id == 0 else 'O'
                return f"Player {next_player}'s turn"
        
        board_gallery, showing_state, show_node_id = self.update_board_gallery(game, show_node_id)
        status = get_updated_status(game)
        output_text = self.output_text  # Update in case the self.output_text was changed
        ai_explanation = self.ai_explanation_components["explanation_output"].value
        explaining_question = self.ai_explanation_components["explaining_question"].value

        adjective = "the best"
        ai_explanation, explaining_question, current_node_id, current_adjective, current_comparison_id = self.explainer_interface.ai_explainer.update_ai_explanation(game, explainer, None, adjective)

        return game, board_gallery, showing_state, status, output_text, ai_explanation, show_node_id, adjective, explaining_question, current_node_id, current_adjective, current_comparison_id

    def update_board_gallery(self, game, node_id=None):
        """
        Get the updated board images based on the current game state.

        :param node_id: The ID of the node to explain
        :type node_id: str
        :return: The updated board gallery, showing state, and node ID
        :rtype: Tuple[gr.Gallery, str, str]
        """
        if game is None:
            return gr.Gallery(), "Start a Game to show the board", None
        elif game.explaining_agent is None:
            return gr.Gallery(), "No explaining agent was found", None
        
        # Determine the node to display and its corresponding board state
        if node_id is not None:
            # If a specific node is requested, fetch it from the explaining agent's core
            if node_id not in game.explaining_agent.core.nodes:
                # If it is not in the core tree, it is not a valid node
                node_id = None
                self.output("Invalid node ID", type="error")
            else:
                # Node is valid, we can retrieve it
                node = game.explaining_agent.core.nodes[node_id]
                parent_state = node.parent_state
                current_id = game.explaining_agent.choice.id

                # Determine if the requested node is the current state or a different node
                if current_id == node_id:
                    board_state = game.model.action_spaces["board"]
                    showing_state = f"Current State ({node_id})"
                else:
                    board_state = node.game_state
                    showing_state = f"{node_id}"

        else: # no node requested or valid
            # If no specific node is requested, use the current choice of the explaining agent
            if game.explaining_agent is not None:
                node_id = game.explaining_agent.choice.id if game.explaining_agent.choice else ""
                parent_state = game.explaining_agent.choice.parent_state if game.explaining_agent.choice else None
            else:
                node_id = None
                parent_state = None
            board_state = game.model.action_spaces["board"]
            showing_state = f"Current State ({node_id})" if node_id else "Current State"

        # After determining the node and board state, we can get the cell images and update the gallery
        def get_cell_image(cell_value, is_changed, i, j):
            """
            Get the appropriate cell image and add the index.
            """
            if cell_value == '' or cell_value == ' ':
                img = self.board_cell_images['empty'].copy()
            else:
                img_key = f"{cell_value}_red" if is_changed else cell_value
                img = self.board_cell_images[img_key].copy()
            
            # Add index to the image
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default().font_variant(size=15)
            draw.text((5, 3), f"{i},{j}", font=font, fill='blue')
            
            return img

        updated_images = []
        for i in range(3):
            for j in range(3):
                cell_value = board_state[i, j]
                is_changed = parent_state is not None and parent_state[i, j] != cell_value
                cell_image = get_cell_image(cell_value, is_changed, i, j)
                updated_images.append(cell_image)
        
        board_gallery = gr.Gallery(
            value=updated_images,
            **self.gallery_settings
        )
        return board_gallery, showing_state, node_id
    
    def update_showing_state(self, game, showing_state):
        """
        Update the showing state label.
        """
        if showing_state is not None:
            showing_state = self.explainer_interface.transform_hyperlink_to_node_id(showing_state)

        if showing_state is not None and showing_state in game.explaining_agent.core.nodes:
            node_id = showing_state
            board_gallery, showing_state, show_node_id = self.update_board_gallery(game, node_id)
        else:
            board_gallery, showing_state, show_node_id = self.update_board_gallery(game)
        
        return board_gallery, showing_state, show_node_id
        
    def create_game(self):
        """
        Create the game instance.
        """
        if self.init_game is not None:
            game = self.init_game
        else:
            game = self.create_game_method()

        if not hasattr(game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the gradio interface.")
        elif not hasattr(game, 'explaining_agent'):
            raise AttributeError("The game instance does not have an 'explaining_agent' attribute, thus it does not support the gradio interface.")

        asyncio.run(game.start_game())
        return game
    
    def restart_game(self, game, explainer):
        """
        Restart the game.
        """
        if game is None:
            raise gr.Error("Game is None")
        game.restart()
        return self.update(game, explainer)

    async def process_move(self, game, explainer, evt: gr.SelectData):
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
            current_player = game.get_current_player()
            sign = game.model.agents[current_player.id, 1]
            inputs = {'what': sign, 'where': (row, col), 'action_space': "board"}
            await current_player.play(game, inputs)
        except Exception as e:
            self.output(str(e), type="error")
            print(f"Detailed error: {type(e).__name__}: {str(e)}")  # For debugging
            print("Full traceback:")
            traceback.print_exc()

        return self.update(game, explainer)


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
