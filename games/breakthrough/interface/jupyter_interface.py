from typing import Dict
import ipywidgets as widgets
from IPython.display import display
import asyncio
import copy

from src.game.interface.jupyter_interface import GameJupyterInterface

class BreakthroughJupyterInterface(GameJupyterInterface):
    """
    Interface for the Breakthrough game in Jupyter notebooks.

    This class handles the game's user interface, including the board display,
    player interactions, and game flow. It provides methods to create and update
    the game board, handle user inputs, and display game status.

    :param game: The Breakthrough game instance
    :type game: Breakthrough
    """
    def __init__(self, game):
        super().__init__(game)
        self.where = {}

    def create_button_click_handler(self, row: int, col: int):
        """
        Create a click handler for a board button.

        Generates a function that handles the click event for a specific button
        on the game board. When clicked, it processes the move if it's a user's turn.

        :param row: Row index of the button
        :type row: int
        :param col: Column index of the button
        :type col: int
        :return: The click handler function
        :rtype: function
        """
        def handle_click(b):
            try:
                current_player = self.game.get_current_player()

                if current_player.id not in self.where: # first click
                    if self.game.model.action_spaces["board"][(row, col)] != self.game.free_label:
                        self.where[current_player.id] = (row, col)
                else: # second click
                    what = (row, col)
                    where = copy.deepcopy(self.where[current_player.id])
                    del self.where[current_player.id]

                    inputs = {'what': what, 'where': where, 'on': "pieces"}
                    asyncio.create_task(current_player.play(self.game, inputs))

            except Exception as e:
                self.output(str(e))

        return handle_click