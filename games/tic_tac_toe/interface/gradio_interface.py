from PIL import Image, ImageDraw, ImageFont
import traceback
import asyncio

from src.game.agents import User
from src.explainable_game_interface.gradio_interface import ExplainableGameGradioInterface

import gradio as gr
from src.explainer.interface.gradio_interface import ExplainerGradioInterface

class TicTacToeGradioInterface(ExplainableGameGradioInterface):
    """
    Interface for the Tic Tac Toe game using Gradio.

    This class handles the game's user interface, including the board display,
    player interactions, game flow, and AI move explanations. It provides methods to create and update
    the game board, handle user inputs, display game status, and explain AI moves.
    """
    @property
    def main_action_space_id(self):
        return "board"
    
    def create_board_cell_images(self):
        """
        Create and store all possible cell images.

        :return: A dictionary with the cell type as key and the image as value.
        :rtype: dict
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
    
    def get_cell_image(self, cell_value, is_changed, i, j):
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
                return f"Game Over! Player {'X' if winner == 0 else 'O'} wins!"
        else:
            next_player = 'X' if game.get_current_player().id == 0 else 'O'
            return f"Player {next_player}'s turn"

    def __init__(self, game, explainer=None, interface_hyperlink_mode=True):
        """
        Initialize the TicTacToeGradioInterface.

        Sets up the game instance and initializes necessary attributes.

        :param game: The TicTacToe game instance
        :type game: TicTacToe
        :param explainer: The explainer instance
        :type explainer: Explainer
        :param interface_hyperlink_mode: Whether to use hyperlink mode in the interface
        :type interface_hyperlink_mode: bool
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' or 'explaining_agent' attributes
        """
        super().__init__(game, 
                         game_title_md="# Tic Tac Toe (vs Alpha-Beta Pruning Minimax)", 
                         action_spaces_to_visualize=[self.main_action_space_id, "agents"],
                         explainer=explainer,
                         interface_hyperlink_mode=interface_hyperlink_mode)

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
