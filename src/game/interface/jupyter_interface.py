from abc import abstractmethod
from typing import Dict
import ipywidgets as widgets
from IPython.display import display

from src.game.interface.interface import GameInterface

class GameJupyterInterface(GameInterface):
    """
    Interface for games in Jupyter notebooks.

    This class handles the game's user interface, including the board display,
    player interactions, and game flow. It provides methods to create and update
    the game board, handle user inputs, and display game status.

    :param game: The game instance
    :type game: Game
    """
    button_x_size = 50
    button_y_size = 50

    def __init__(self, game):
        """
        Initialize the GameJupyterInterface.

        Sets up the game instance, buttons for the board, status label, and output area.
        Checks if the game instance has the required methods for the interface.

        :param game: The game instance
        :type game: Game
        :raises AttributeError: If the game instance doesn't have a 'get_current_player' method
        """
        super().__init__(game)
        if not hasattr(game, 'get_current_player'):
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

        Generates a grid of buttons representing the game board,
        along with a status label and an output area for game messages.

        :return: A vertical box containing the game board, status label, and output area
        :rtype: widgets.VBox
        """
        main_action_space_shape = self.game.model.action_spaces[self.game.main_action_space_id].shape
        for i in range(main_action_space_shape[0]):
            for j in range(main_action_space_shape[1]):
                button = widgets.Button(
                    description='', 
                    layout=widgets.Layout(
                        width=f'{self.button_x_size}px', 
                        height=f'{self.button_y_size}px', 
                        margin='0px',
                        border='1px solid black'
                    )
                )
                button.on_click(self.create_button_click_handler(i, j))
                self.buttons[(i, j)] = button

        self.status_label = widgets.Label()
        self.board_output = widgets.Output()
        
        board_widget = widgets.GridBox(
            children=list(self.buttons.values()),
            layout=widgets.Layout(
                grid_template_columns=f"repeat({main_action_space_shape[1]}, auto)",
                grid_gap='0px',
                width=f'{self.button_x_size * main_action_space_shape[1]}px',
                height=f'{self.button_y_size * main_action_space_shape[0]}px'
            )
        )
        return widgets.VBox([board_widget, self.status_label, self.board_output])

    @abstractmethod
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
        pass
        # As an example, here is the implementation for the Tic Tac Toe game:
        # def handle_click(b):
        #     try:
        #         current_player = self.game.get_current_player()
        #         sign = self.game.model.agents[current_player.id, 0]
        #         inputs = {'what': sign, 'where': (row, col), 'on': "board"}
        #         asyncio.create_task(current_player.play(self.game, inputs))

        #     except Exception as e:
        #         self.output(str(e))

        # return handle_click
    
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
    
    def update(self) -> None:
        """
        Update the game state in the interface.

        Refreshes the board display to reflect the current game state,
        updates button descriptions, and changes the status label based on
        whether the game has ended or it's the next player's turn.
        """
        # Update board buttons
        board_state = self.game.model.action_spaces[self.game.main_action_space_id]
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
            self.status_label.value = f"Game Over! Player {self.game.model.agents[winner, 0]} wins!"

    def update_next_player_status(self) -> None:
        """
        Update the status label for the next player's turn.

        Changes the status label to indicate which player should make
        the next move.
        """
        next_player = self.game.model.agents[self.game.get_current_player().id, 0]
        self.status_label.value = f"Player {next_player}'s turn"

    def clear_board_output(self) -> None:
        """
        Clear the board output in the Jupyter notebook interface.

        Removes any existing text from the output area below the game board.
        """
        if self.board_output:
            self.board_output.clear_output()