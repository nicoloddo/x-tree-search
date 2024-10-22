from abc import ABC, abstractmethod

from PIL import Image, ImageDraw, ImageFont
import traceback
import asyncio

from src.game.agents import User
from src.game.interface.gradio_interface import GameGradioInterface

import gradio as gr
from src.explainer.interface.gradio_interface import ExplainerGradioInterface

class ExplainableGameGradioInterface(GameGradioInterface):
    """
    Interface for explainable games using Gradio.

    This class handles the game's user interface, including the game state display,
    player interactions, game flow, and AI move explanations. It provides methods to create and update
    the game state, handle user inputs, display game status, and explain AI moves.
    """
    
    def __init__(self, game, game_title_md, action_spaces_to_visualize, explainer=None, interface_hyperlink_mode=True):
        """
        Initialize the ExplainableGameGradioInterface.

        Sets up the game instance and initializes necessary attributes.

        :param game: The game instance
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :param interface_hyperlink_mode: Whether to use hyperlink mode in the interface
        :type interface_hyperlink_mode: bool
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' or 'explaining_agent' attributes
        """
        if not hasattr(game, 'explaining_agent'):
            raise AttributeError("The game instance does not have an 'explaining_agent' attribute, thus it does not support the gradio interface.")
        if not hasattr(game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the gradio interface.")
        super().__init__(game, 
                         game_title_md=game_title_md, 
                         action_spaces_to_visualize=action_spaces_to_visualize)
        
        self.ai_explanation_components = None
        self.explainer = explainer
        self.explainer_interface = ExplainerGradioInterface(explainer=self.explainer, explain_in_hyperlink_mode=interface_hyperlink_mode)

    @property
    @abstractmethod
    def main_action_space_id(self):
        """
        Get the main action space ID.

        :return: The main action space ID
        :rtype: str
        """
        pass

    @abstractmethod
    def get_updated_status(self, game):
        """
        Get the updated status based on the current game state.

        :param game: The game state
        :type game: Game
        :return: The updated status text
        :rtype: str
        """
        pass

    def create_interface(self):
        """
        Create the interface for the explainable game.
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
                """, # Perfectionates the game state display
            fill_width=True) as demo:
            game_state = gr.State(self.game)
            explainer_state = gr.State(self.explainer)

            with gr.Tabs():
                with gr.TabItem("Game and Explain", id=self.explainer_interface.tab_ids["other"] + 0):
                    with gr.Row(equal_height=False):
                        with gr.Column(scale=1):
                            game_components = super().build_interface()
                            main_board_gallery = game_components["board_gallery"][self.main_action_space_id]
                    
                        with gr.Column(scale=2):
                            gr.Markdown("# AI Move Explanation")
                            self.ai_explanation_components = self.explainer_interface.interface_builder.build_ai_explanation_components(
                                game_state,
                                explainer_state,
                                toggles={"skip_score_toggle": ("Skip Score Statement (the explainer is designed around skipping the score statement, problems may arise when this is disabled)", True)},
                                additional_info="P.S. To visualize a move on the board you can drag and drop the move from the explanation to the \"Showing\" widget."
                            )

                with gr.TabItem("Visualize Decision Tree", self.explainer_interface.tab_ids["visualize_decision_tree"]):
                    visualize_decision_tree_components = self.explainer_interface.interface_builder.build_visualize_decision_tree_components(game_state)

                with gr.TabItem("Visualize Framework", self.explainer_interface.tab_ids["visualize"]):
                    visualize_components = self.explainer_interface.interface_builder.build_visualize_components()
                
                with gr.TabItem("Settings", self.explainer_interface.tab_ids["settings"]):
                    explainer_settings_components = self.explainer_interface.interface_builder.build_explainer_settings_components()

            #*********************************
            # 2. Handle components connections 
            #
            self.explainer_interface.interface_builder.connect_components({**self.ai_explanation_components, **visualize_components, 
                                                                           **visualize_decision_tree_components, **explainer_settings_components}, 
                                                                           game_state, explainer_state)

            all_available_outputs = [game_state, 
                                     main_board_gallery, game_components["showing_state"], game_components["status"], 
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

            game_components["showing_state"].change(
                self.update_showing_state,
                inputs=[game_state, game_components["showing_state"]],
                outputs=[main_board_gallery, game_components["showing_state"], self.ai_explanation_components["id_input"]]
            )
            
            main_board_gallery.select(
                self.process_move,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs
            )

            game_components["show_current_state_button"].click(
                self.update_board_gallery,
                inputs=[game_state],
                outputs=[main_board_gallery, game_components["showing_state"], self.ai_explanation_components["id_input"]]
            )

            game_components["restart_game_button"].click(
                self.restart_game,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs
            )

            def toggle_skip_score(game, explainer, skip_score: bool, current_node_id: str, current_adjective: str, current_comparison_id: str, explanation_depth: int):
                """
                Toggle the skip score statement setting and update the explanation.
                """
                explainer.frameworks['highlevel'].get_adjective('score').skip_statement = skip_score

                ai_explanation, explaining_question, _, _, _ = self.explainer_interface.ai_explainer.update_ai_explanation(game, explainer, current_node_id, current_adjective, current_comparison_id, explanation_depth)
                
                return ai_explanation, explaining_question

            skip_score_toggle = self.ai_explanation_components["skip_score_toggle"]
            skip_score_toggle.change(
                toggle_skip_score,
                inputs=[game_state, explainer_state, skip_score_toggle, 
                        self.ai_explanation_components["current_node_id"], 
                        self.ai_explanation_components["current_adjective"], 
                        self.ai_explanation_components["current_comparison_id"], 
                        self.ai_explanation_components["explanation_depth"]],
                outputs=[self.ai_explanation_components["explanation_output"], self.ai_explanation_components["explaining_question"]]
            )

            # Initial update
            demo.load(
                self.on_load,
                inputs=[game_state, explainer_state],
                outputs=all_available_outputs,
            )

        return demo

    def on_load(self, game, explainer, request: gr.Request):
        """
        On load event handler.

        :param game: The game state
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :param request: The Gradio request object
        :type request: gr.Request
        :return: Updated game state and interface components
        """
        self.explainer_interface.on_load(request)
        super().on_load(game)
        return self.update(game, explainer)
    
    def update(self, game, explainer, show_node_id=None):
        """
        Update the game state in the interface.

        Refreshes the game state display, status, and output based on the current game state.
        Consider that due to Gradio's event handling approach, this method will not do anything when
        called directly, but it rather need to be attached to an event to be applied correctly.

        :param game: The game state
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :param show_node_id: The ID of the node to show, if any
        :type show_node_id: str, optional
        :return: Updated game state and interface components
        """
        if game is None:
            return gr.Gallery(), "Start a Game to show the board", None, None, None, None, None, None
        
        board_gallery, showing_state, show_node_id = self.update_board_gallery(game, show_node_id)
        status = self.get_updated_status(game)
        ai_explanation = self.ai_explanation_components["explanation_output"].value
        explaining_question = self.ai_explanation_components["explaining_question"].value

        adjective = "the best"
        ai_explanation, explaining_question, current_node_id, current_adjective, current_comparison_id = self.explainer_interface.ai_explainer.update_ai_explanation(game, explainer, None, adjective)

        return game, board_gallery, showing_state, status, ai_explanation, show_node_id, adjective, explaining_question, current_node_id, current_adjective, current_comparison_id

    def update_board_gallery(self, game, node_id=None):
        """
        Get the updated game state images based on the current game state.

        :param game: The game state
        :type game: Game
        :param node_id: The ID of the node to explain
        :type node_id: str, optional
        :return: The updated game state gallery, showing state, and node ID
        :rtype: Tuple[gr.Gallery, str, str]
        """
        # TODO: Make this more general to update all the board galleries in the game
        # and move it to the GameGradioInterface class.
        if game is None:
            return gr.Gallery(), "Start a Game to show the board", None
        elif game.explaining_agent is None:
            return gr.Gallery(), "No explaining agent was found", None
        
        # Determine the node to display and its corresponding game state
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
                    board_state = game.model.action_spaces[self.main_action_space_id]
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
            board_state = game.model.action_spaces[self.main_action_space_id]
            showing_state = f"Current State ({node_id})" if node_id else "Current State"

        updated_images = []
        for i in range(board_state.shape[0]):
            for j in range(board_state.shape[1]):
                cell_value = board_state[i, j]
                is_changed = parent_state is not None and parent_state[i, j] != cell_value
                cell_image = self.get_cell_image(cell_value, is_changed, i, j)
                updated_images.append(cell_image)
        
        board_gallery = gr.Gallery(
            value=updated_images,
            **self.board_gallery_settings[self.main_action_space_id]
        )
        return board_gallery, showing_state, node_id
    
    def update_showing_state(self, game, showing_state):
        """
        Update the showing state label.

        :param game: The game state
        :type game: Game
        :param showing_state: The current showing state
        :type showing_state: str
        :return: Updated game state gallery, showing state, and node ID
        :rtype: Tuple[gr.Gallery, str, str]
        """
        if showing_state is not None:
            showing_state = self.explainer_interface.transform_hyperlink_to_node_id(showing_state)

        if showing_state is not None and showing_state in game.explaining_agent.core.nodes:
            node_id = showing_state
            board_gallery, showing_state, show_node_id = self.update_board_gallery(game, node_id)
        else:
            board_gallery, showing_state, show_node_id = self.update_board_gallery(game)
        
        return board_gallery, showing_state, show_node_id
    
    def get_updated_status(self, game):
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
                return f"Game Over! Player {game.model.agents[winner, 1]} wins!"
        else:
            next_player = game.model.agents[game.get_current_player().id, 1]
            return f"Player {next_player}'s turn"
    
    def restart_game(self, game, explainer):
        """
        Restart the game.

        :param game: The game state
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :return: Updated game state and interface components
        """
        if game is None:
            raise gr.Error("Game is None")
        game.restart()
        return self.update(game, explainer)