from abc import abstractmethod

from PIL import Image, ImageDraw, ImageFont
import traceback
import asyncio

from src.game.agents import User
from src.game.interface.interface import GameInterface

import gradio as gr
from src.explainer.interface.gradio_interface import ExplainerGradioInterface

class GameGradioInterface(GameInterface):
    """
    Parent interface for the games using Gradio.
    """
    @abstractmethod
    def create_board_cell_images(cls):
        """
        Create and store all possible cell images.

        :return: A dictionary with the cell type as key and the image as value.
        :rtype: dict
        """

    def __init__(self, game, game_title_md="# Game", action_spaces_to_visualize=[]):
        """
        Initialize the GameGradioInterface.

        Sets up the game instance and initializes necessary attributes.

        :param game: The game instance
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :param interface_hyperlink_mode: Whether to use hyperlink mode in the interface
        :type interface_hyperlink_mode: bool
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' or 'explaining_agent' attributes
        """
        super().__init__(game)
        if not hasattr(game, 'get_current_player'):
            raise AttributeError("The game instance does not have a 'get_current_player' method, thus it does not support the gradio interface.")
    
        self.game_title_md = game_title_md
        self.board_cell_images = self.create_board_cell_images()
        self.board_gallery_settings = {
            action_space_id: {
                "columns": action_space.shape[1],  # Number of columns from the action space dimensions
                "rows": action_space.shape[0],     # Number of rows from the action space dimensions
                "height": "max-content",
                "allow_preview": False,
                "show_label": False,
                "elem_id": action_space_id  # Use the action space id as the element id
            }
            for action_space_id, action_space in game.gm.action_spaces.items() if action_space_id in action_spaces_to_visualize
        }

    @abstractmethod
    def restart_game(self):
        """
        Restart the game.
        """
        pass

    @abstractmethod
    def update(self):
        """
        Update the game state in the interface.
        """
        pass
    
    def build_interface(self):
        """
        Build the components to display the Game.
        Build it insiide a gr.Blocks()
        """
        components = {}

        components["title"] = gr.Markdown(self.game_title_md)
        with gr.Row():
            components["status"] = gr.Textbox(label="Status", value="Starting game...", scale=1)
            components["showing_state"] = gr.Textbox(label="Showing (drag and drop to change)", value="Starting game...", scale=1, interactive=True)
        with gr.Row():
            components["restart_game_button"] = gr.Button("Restart Game", scale=1)
            components["show_current_state_button"] = gr.Button("Return to Current State", scale=1)

        components["board_gallery"] = {}
        for action_space_id, settings in self.board_gallery_settings.items():
            with gr.Tab(action_space_id):
                components["board_gallery"][action_space_id] = gr.Gallery(
                    value=[],
                    **settings
                )
        
        return components
    
    def start(self, share_gradio=False):
        """
        Start the game interface.

        Initializes the game state and launches the Gradio interface.

        :param share_gradio: Whether to share the Gradio interface publicly
        :type share_gradio: bool
        """
        self.started = True
        demo = self.create_interface()
        demo.launch(share=share_gradio)

    def on_load(self, game):
        """
        On load event handler.
        Call this in a load event of the main interface.

        :param game: The game state
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :return: Updated game state and interface components
        """
        asyncio.run(game.start_game())
    
    def output(self, text: str, type: str = "info"):
        """
        Handle output information.

        :param text: The text to display in the output area
        :type text: str
        :param type: The type of output (info, error, or warning)
        :type type: str
        """
        if len(text) == 0:
            return
        
        if type == "info":
            gr.Info(text)
        elif type == "error":
            gr.Warning(text)
        elif type == "warning":
            gr.Warning(text)
        else:
            raise ValueError(f"Invalid type {type}")

