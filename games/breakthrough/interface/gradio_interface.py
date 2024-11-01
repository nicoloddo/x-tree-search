from PIL import Image, ImageDraw, ImageFont
import asyncio
import traceback
import gradio as gr
import copy

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
        for cell_type in ['empty', 'w', 'b', 'w_changed', 'b_changed']:
            img = Image.new('RGB', (cell_size, cell_size), color='beige')
            draw = ImageDraw.Draw(img)
            
            # Draw border
            draw.rectangle([0, 0, cell_size-1, cell_size-1], outline='black', width=2)
            
            if cell_type != 'empty':
                piece_color = 'coral' if cell_type.startswith('w') else 'black'
                outline_color = 'cyan' if cell_type.endswith('_changed') else piece_color
                
                # Draw the piece (a filled circle)
                padding = 10
                draw.ellipse([padding, padding, cell_size-padding, cell_size-padding], fill=piece_color, outline=outline_color, width=2)
            
            images[cell_type] = img
        return images
    
    def get_cell_image(self, cell_value, is_changed, i, j):
        """
        Get the appropriate cell image and add the index.
        """
        if cell_value == '' or cell_value == ' ':
            img = self.board_cell_images['empty'].copy()
        else:
            img_key = f"{cell_value}_changed" if is_changed else cell_value
            img = self.board_cell_images[img_key].copy()
        
        # Add index to the image
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default().font_variant(size=15)
        draw.text((5, 3), f"{i},{j}", font=font, fill='blue')
        
        return img

    def __init__(self, game, explainer=None, interface_hyperlink_mode=True, *, game_title_md="# Breakthrough vs AlphaBeta"):
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
        help_md = """
        Click on a piece to select it.
        Click on a cell to move the selected piece to that cell.
        If you want to change the piece to move, make an invalid move to deselect the piece.

        If the piece you want to select is in a cell with the orange border (previously selected cell), you won't be able to click on it. 
        Click on an empty space so that the orange border goes to the empty cell before clicking on the piece.
        """
        game_board_side_size =  game.action_spaces["board"].shape[0]
        if game_board_side_size == 6:
            game_explanation_interface_ratio = "3:4"
        elif game_board_side_size == 8:
            game_explanation_interface_ratio = "1:1"
        else:
            game_explanation_interface_ratio = "1:1"

        super().__init__(game, 
                         game_title_md=game_title_md, 
                         action_spaces_to_visualize=[self.main_action_space_id, "agents"],
                         explainer=explainer,
                         interface_hyperlink_mode=interface_hyperlink_mode,
                         game_explanation_ratio=game_explanation_interface_ratio,
                         help_md=help_md)
        self.where = {}
        
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
            row, col = index // game.action_spaces[self.main_action_space_id].shape[1], index % game.action_spaces[self.main_action_space_id].shape[1]

            current_player = game.get_current_player()

            if current_player.id not in self.where: # first click
                if game.action_spaces["board"][(row, col)] != game.free_label:
                    self.where[current_player.id] = (row, col)
            else: # second click
                what = (row, col)
                where = copy.deepcopy(self.where[current_player.id])
                del self.where[current_player.id]

                inputs = {'what': what, 'where': where, 'on': "board"}
                await current_player.play(game, inputs) # User move
                self.update(game, explainer)
                await game.continue_game() # AI move

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
