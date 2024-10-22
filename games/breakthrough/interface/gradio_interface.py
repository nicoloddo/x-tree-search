from PIL import Image, ImageDraw, ImageFont
import asyncio
import traceback
import gradio as gr

from src.game.agents import User
from src.explainable_game_interface.gradio_interface import ExplainableGameGradioInterface

class BreakthroughGradioInterface(ExplainableGameGradioInterface):
    """
    Interface for the Breakthrough game using Gradio.

    This class handles the game's user interface, including the board display,
    player interactions, game flow, and AI move explanations. It provides methods to create and update
    the game board, handle user inputs, display game status, and explain AI moves.
    """
    @property
    def main_action_space_id(self):
        return "board"
    
    def create_board_cell_images(self):
        """
        Create and store all possible cell images for Breakthrough.

        :return: A dictionary with the cell type as key and the image as value.
        :rtype: dict
        """
        cell_size = 100
        images = {}
        for cell_type in ['empty', 'white', 'black', 'white_red', 'black_red']:
            img = Image.new('RGB', (cell_size, cell_size), color='beige' if (cell_type == 'empty' or cell_type.startswith('white')) else 'brown')
            draw = ImageDraw.Draw(img)
            
            # Draw border
            draw.rectangle([0, 0, cell_size-1, cell_size-1], outline='black', width=2)
            
            if cell_type != 'empty':
                piece_color = 'white' if cell_type.startswith('white') else 'black'
                outline_color = 'red' if cell_type.endswith('_red') else piece_color
                
                # Draw the piece (a filled circle)
                padding = 10
                draw.ellipse([padding, padding, cell_size-padding, cell_size-padding], fill=piece_color, outline=outline_color, width=3)
            
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

    def __init__(self, game, explainer=None, interface_hyperlink_mode=True, *, game_title_md="# Breakthrough"):
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
                         game_title_md=game_title_md, 
                         action_spaces_to_visualize=[self.main_action_space_id, "agents"],
                         explainer=explainer,
                         interface_hyperlink_mode=interface_hyperlink_mode)
        
    async def process_move(self, game, explainer, evt: gr.SelectData):
        """
        Process a move made by the current player.

        :param game: The game state
        :type game: Game
        :param explainer: The explainer instance
        :type explainer: Explainer
        :param evt: The event data containing the selected index
        :type evt: gr.SelectData
        :return: Updated game state and interface components
        """
        try:
            index = evt.index
            row, col = index // game.model.action_spaces[self.main_action_space_id].shape[1], index % game.model.action_spaces[self.main_action_space_id].shape[1]
            current_player = game.get_current_player()
            action = game.model.agents[current_player.id, 1]
            inputs = {'what': action, 'where': (row, col), 'action_space': self.main_action_space_id}
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
