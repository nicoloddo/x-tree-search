import numpy as np
import copy

from src.game.utils import parse_where_input as ut_parse_where_input
from src.game.game import Game, GameModel
from src.game.game_model import ActionSpace
from src.game.agents import User
from src.game.interface.cmd_interface import GameCmdInterface
from games.breakthrough.interface.jupyter_interface import BreakthroughJupyterInterface

FREE_LABEL = ' '
class Breakthrough(Game):
    free_label = FREE_LABEL
    idx_to_color = {0: 'w', 1: 'b'}
    color_to_idx = {value: key for key, value in idx_to_color.items()}
    color_side = {0: idx_to_color[1], -1: idx_to_color[0]} # 0 has the pieces on the top, -1 has the pieces on the bottom
    board_shape = (6, 6)

    @classmethod
    def game_state_translator(cls, pieces_state): # pieces state to board state
        """
        Convert the pieces state to the board state.
        """
        if not pieces_state.shape == (12, 2):
            raise ValueError("The state we are trying to translate is not in the shape of a pieces state.")

        board_state = np.ndarray((cls.board_shape), dtype=object)
        board_state.fill(FREE_LABEL)

        for player_idx in range(2):
            for piece_idx in range(12):
                piece_coords = pieces_state[piece_idx, player_idx]
                if piece_coords != "(-1, -1)":  # Check if the piece is still on the board
                    row, col = eval(piece_coords)
                    color = cls.idx_to_color[player_idx]
                    board_state[row, col] = color

        return board_state

    def __init__(self, *, players=None, interface_mode='gradio', interface_hyperlink_mode=True, fast_check_rules=True):
        """
        Initialize the Breakthrough game.

        :param interface_mode: The interface mode to use for the game.
        :type interface_mode: str
        :param players: The players to use for the game.
        :type players: list
        :param fast_check_rules: Whether to use fast check rules for the Game Model. This will stop the check of rules as soon as a rule is violated.
        :type fast_check_rules: bool
        """
        _child_init_params = {
            'players': players,
            'interface_mode': interface_mode,
            'interface_hyperlink_mode': interface_hyperlink_mode
        }
        super().__init__(_child_init_params, players=players, main_action_space_id="board", tree_action_space_id="pieces", fast_check_rules=fast_check_rules,
                         where_question="Insert the coordinates of the piece you want to move [insert 'exit' to exit] [click enter with no input to refresh]: ",
                         what_question="Insert the coordinates of the destination space [insert 'exit' to exit] [click enter with no input to refresh]: ",
                         parse_where_input=ut_parse_where_input,
                         parse_what_input=ut_parse_where_input) # The what input is also in coordinates format
        
        self.interface_mode = interface_mode
        self.select_interface(interface_mode, interface_hyperlink_mode)

    def select_interface(self, interface_mode, interface_hyperlink_mode):
        """
        Select the interface for the game.

        :param interface_mode: The interface mode to use for the game.
        :type interface_mode: str
        """
        if interface_mode == 'cmd':
            print("Be aware that the cmd interface is not fully maintained and might not work as expected.")
            self.interface = GameCmdInterface(self)
        elif interface_mode == 'jupyter':
            self.interface = BreakthroughJupyterInterface(self)
        elif interface_mode == 'gradio':
            self.interface = None # Interface is created in the app.py file
        else:
            raise ValueError(f"Unsupported interface mode: {interface_mode}")

    async def start_game(self, share_gradio=False):
        await self.process_turn()  

        if self.interface_mode == 'cmd':
            self.interface.start()
        elif self.interface_mode == 'jupyter':
            self.interface.start()
        elif self.interface_mode == 'gradio':
            pass # Create and start the interface externally
        else:
            raise ValueError(f"Unsupported interface mode: {self.interface_mode}")
    
    @property
    def node_string_format(self):
        return "{who_game_identifier}{what_before} in {what}"
    
    def constrain_action_around_piece(self, what, what_before):
        what = eval(what)
        what_before = eval(what_before)
        return what != what_before and what != (-1, -1) and abs(what[0] - what_before[0]) <= 1 and abs(what[1] - what_before[1]) <= 1
    
    def expansion_constraints_self(self, agent_id):
        """Get expansion constraints for the current player.
        Expansion constraints limits the search of available moves,
        thus reducing computational costs."""
        return {'who': lambda who, agent: who == agent_id,
                'what': self.constrain_action_around_piece}
    
    def expansion_constraints_other(self, agent_id):
        "Get expansion constraints for the other player"
        not_agent_ids = [key for key in self.players.keys() if key != agent_id]
        if len(not_agent_ids) == 1:
            other_id = not_agent_ids[0]
            return {'who': lambda who, agent: who == other_id,
                    'what': self.constrain_action_around_piece}
        else:
            raise ValueError("A Breakthrough game should have a maximum of two players.")
        
    def _get_piece_index(self, game_model, piece_coordinates, color=None):
        i_range = range(game_model.action_spaces["pieces"].shape[0])
        if color is None:
            color_range = range(game_model.action_spaces["pieces"].shape[1])
        else:
            color_range = range(self.color_to_idx[color], self.color_to_idx[color]+1) # only the pieces of the given color

        for i in i_range:
            for j in color_range:
                piece_position = game_model.action_spaces["pieces"][i, j]
                piece_coordinates_str = str(piece_coordinates)
                if piece_position == piece_coordinates_str:
                    return i, j
        raise ValueError(f"Piece not found in position {piece_coordinates}")
    
    def _game_model_definition(self) -> GameModel:
        gm = GameModel( 
        agents_number=2, default_agent_features=[self.idx_to_color[0], 'starter'], additional_agent_features=[[self.idx_to_color[1]], ['not starter']], 
        agent_features_descriptions="2 players with feature 1 indicating who is starting, and feature 2 indicating their pieces' color.",
        game_name="breakthrough")
        gm.add_action_space("board", dimensions=list(self.board_shape), default_labels=[FREE_LABEL], additional_labels=[['w', 'b']], 
                            dimensions_descriptions="6x6 board.")
        gm.add_action_space("pieces", dimensions=[12, 2], default_labels=[str((-1, -1))], additional_labels=[[str((x, y)) for x in range(self.board_shape[0]) for y in range(self.board_shape[1])]], 
                            dimensions_descriptions="12 pieces x 2 sides (black and white). As values we have the coordinates of the pieces. -1 means that the piece is not on the board.")

        # Disable actions on the agent feature space.
        gm.disable_actions(on="agent")
        gm.disable_actions(on="board")
        gm.agents[1, 0] = self.idx_to_color[1]
        gm.agents[1, 1] = 'not starter'

        # Initialize the board and pieces
        first_two_rows_color = self.color_side[0]
        last_two_rows_color = self.color_side[-1]

        # Set up the board
        for i in range(2):
            for j in range(6):
                gm.action_spaces["board"][i, j] = first_two_rows_color
                gm.action_spaces["board"][5-i, j] = last_two_rows_color

        # Set up the pieces
        first_color_idx = self.color_to_idx[first_two_rows_color]
        last_color_idx = self.color_to_idx[last_two_rows_color]

        for i in range(12):
            row = i // 6
            col = i % 6
            gm.action_spaces["pieces"][i, first_color_idx] = str((row, col))
            gm.action_spaces["pieces"][i, last_color_idx] = str((5-row, col))

        # Set Endgame
        def breakthrough_endgame(game):
            board = game.action_spaces["board"]
            # Check if any white piece reached the last row
            if any(cell == self.color_side[0] for cell in board[-1]):
                return True
            
            # Check if any black piece reached the first row
            if any(cell == self.color_side[-1] for cell in board[0]):
                return True
            
            # Check if one player has no pieces left
            white_pieces = np.sum(board == 'w')
            black_pieces = np.sum(board == 'b')
            if white_pieces == 0 or black_pieces == 0:
                return True
            
            # If no winning condition is met, the game continues
            return False

        gm.set_endgame(breakthrough_endgame)

        # what: the new coordinates of the piece
        # where: the old coordinates of the piece
        # Both are already parsed into a tuple of coordinates

        # Set rules
        gm.action_is_violation_if(lambda who, where, what, game: not game.started and game.agents[who][1] != 'starter', rule_description="This is not the starting player and this is the first turn.")
        gm.action_is_violation_if(lambda who, where, what, game: game.started and who == game.actions[-1]['who'], rule_description="Players cannot play two times consecutively.")
        gm.action_is_violation_if(lambda who, where, what, game: game.agents[who][0] != game.action_spaces["board"][where], "pieces", rule_description="Players cannot move pieces of the other player.")
        gm.action_is_violation_if(
            lambda who, where, what, game: game.action_spaces["board"][what] == game.agents[who][0],
            rule_description="Players cannot move to a space occupied by their own piece."
        )
        gm.action_is_violation_if(
            lambda who, where, what, game: False if abs(what[0] - where[0]) == abs(what[1] - where[1]) else game.action_spaces["board"][what] != game.agents[who][0] and game.action_spaces["board"][what] != self.free_label,
            "pieces",
            rule_description="Players cannot move to a space occupied by an enemy piece, unless it's a diagonal movement."
        )
        gm.action_is_violation_if(
            lambda who, where, what, game: abs(what[0] - where[0]) > 1 or abs(what[1] - where[1]) > 1,
            "pieces",
            rule_description="A piece cannot move more than one space at a time."
        )
        gm.action_is_violation_if(
            lambda who, where, what, game: (what[0] - where[0]) > 0 if who == 0 else (what[0] - where[0]) < 0,
            "pieces",
            rule_description="Pieces cannot move to a space behind it."
        )
        gm.action_is_violation_if(
            lambda who, where, what, game: abs(what[0] - where[0]) == 0 and abs(what[1] - where[1]) > 0,
            "pieces",
            rule_description="A piece cannot move horizontally."
        )
        gm.action_is_violation_if(
            lambda who, where, what, game: (abs(what[1] - where[1]) + abs(what[0] - where[0])) == 0,
            "pieces",
            rule_description="Making a piece stay in place is not a valid move."
        )

        def piece_eating(action, game):
            eaten_color = self.idx_to_color[1 if action['who'] == 0 else 0]
            board_coordinates = self.parse_what_input(action['what'])
            eaten_piece_index = self._get_piece_index(game, board_coordinates, eaten_color)
            game.action_spaces["pieces"][eaten_piece_index] = str((-1, -1))
        gm.action_trigger_consequence_if(
            lambda who, where, what, game: game.action_spaces["board"][what] != FREE_LABEL and game.agents[who][0] != game.action_spaces["board"][what],
            consequence=piece_eating, 
            rule_description="If the destination space is occupied by an enemy piece, the enemy piece is eaten.")
        
        # Board sync consequence must be executed last
        def piece_movement_board_sync(action, game):
            prev_board_coordinates = game.parse_what_input(action['what_before'])
            new_board_coordinates = game.parse_what_input(action['what'])
            piece = game.action_spaces["board"][prev_board_coordinates]
            game.action_spaces["board"][prev_board_coordinates] = FREE_LABEL
            game.action_spaces["board"][new_board_coordinates] = piece
        gm.action_trigger_consequence_if(
            lambda who, where, what, game: what != where,
            action_space_id="pieces",
            consequence=piece_movement_board_sync, 
            rule_description="Sync the change in coordinates of the piece with the board.")

        return gm
    
    def act(self, action) -> None:
        if action['on'] == "board":
            piece_index = self._get_piece_index(self.model, action['where'])
        elif action['on'] == "pieces":
            piece_index = action['where']
        else:
            raise ValueError(f"Unsupported action space: {action['on']}")

        return_broken_rule_string = self.interface_mode == 'gradio'
        action_dict, broken_rule_string = self.model.action("pieces", action['who'], piece_index, action['what'], return_broken_rule_string=return_broken_rule_string)
        if broken_rule_string:
            raise ValueError(broken_rule_string)
    
    def winner(self):
        board = self.model.action_spaces["board"]

        # Check if any white piece reached the last row
        if any(cell == self.color_side[0] for cell in board[-1]):
            return self.color_to_idx['w']
        
        # Check if any black piece reached the first row
        if any(cell == self.color_side[-1] for cell in board[0]):
            return self.color_to_idx['b']
        
        # Check if one player has no pieces left
        white_pieces = np.sum(board == 'w')
        black_pieces = np.sum(board == 'b')
        if white_pieces == 0:
            return self.color_to_idx['b']
        elif black_pieces == 0:
            return self.color_to_idx['w']

        return None  # No winner yet
    
    def get_current_player(self):
        """
        Get the current player.

        :return: The current player
        :rtype: Player class
        """
        if not self.started:
            return next(player for id, player in self.players.items() if self.model.agents[id, 1] == 'starter')
        else:
            last_player = self.model.actions[-1]['who']
            return next(player for player in self.players.values() if player.id != last_player) 
    
    """Turn taking logic"""
    async def process_turn(self) -> None:
        """
        Process a single turn in the game.
        """
        current_player = self.get_current_player()

        if not isinstance(current_player, User): # User is handled by the interface
            await current_player.play(self)
            if self.interface is not None and self.interface.started:
                self.interface.output("")

        if self.interface is not None and self.interface.started:
            self.interface.update()

    async def continue_game(self) -> None:
        """
        Continue the game after a move has been made.
        """
        if self.interface is not None:
            self.interface.update()
        if not self.ended:
            await self.process_turn()
