import numpy as np

from src.game.game import Game, GameModel
from src.game.agents import User
from .interface.jupyter_interface import TicTacToeJupyterInterface
from src.game.interface.cmd_interface import GameCmdInterface

FREE_LABEL = ' '
class TicTacToe(Game):
    def __init__(self, *, players=None, interface_mode='gradio', interface_hyperlink_mode=True, fast_check_rules=True):
        """
        Initialize the TicTacToe game.

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
        super().__init__(_child_init_params, players=players, main_action_space_id="board", fast_check_rules=fast_check_rules, ask_what=False)
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
            if interface_hyperlink_mode:
                raise ValueError("Interface hyperlink mode is not supported for Jupyter interface.")
            self.interface = TicTacToeJupyterInterface(self)
        elif interface_mode == 'gradio':
            self.interface = None # Interface is created in the app.py file
        else:
            raise ValueError(f"Unsupported interface mode: {interface_mode}")
        
    async def start_game(self, share_gradio=False):
        super().check_start()
        await self.process_turn()  

        if self.interface_mode == 'cmd':
            self.interface.start()
        elif self.interface_mode == 'gradio':
            pass # Create and start the interface externally
        elif self.interface_mode == 'jupyter':
            self.interface.start()
        else:
            raise ValueError(f"Unsupported interface mode: {self.interface_mode}")

    @property
    def node_string_format(self):
        return "{what} in {where}"
    
    def expansion_constraints_self(self, agent_id):
        """Get expansion constraints for the current player.
        Expansion constraints limits the search of available moves,
        thus reducing computational costs."""
        return {'who': lambda who, agent: who == agent_id}
    
    def expansion_constraints_other(self, agent_id):
        "Get expansion constraints for the other player"
        not_agent_ids = [key for key in self.players.keys() if key != agent_id]
        if len(not_agent_ids) == 1:
            other_id = not_agent_ids[0]
            return {'who': lambda who, agent: who == other_id}
        else:
            raise ValueError("A TicTacToe game should have a maximum of two players.")
    
    def _game_model_definition(self) -> GameModel:
        gm = GameModel( 
        agents_number=2, default_agent_features=['X', 'starter'], additional_agent_features=[['O'], ['not starter']], 
        agent_features_descriptions="2 players with feature 1 indicating who is starting, and feature 2 indicating their symbol.",
        game_name="tic-tac-toe")
        gm.add_action_space("board", dimensions=[3, 3], default_labels=[FREE_LABEL], additional_labels=[['X', 'O']], dimensions_descriptions="3x3 board.")

        # Disable actions on the agent feature space.
        gm.disable_actions(on="agent")
        gm.agents[1, 0] = 'O'
        gm.agents[1, 1] = 'not starter'

        # Set Endgame
        def tic_tac_toe_endgame(game):
            board = game.action_spaces["board"]
            # Check rows for winning condition
            for row in board:
                if row[0] == row[1] == row[2] != FREE_LABEL:
                    return True

            # Check columns for winning condition
            for col in range(3):
                if board[0][col] == board[1][col] == board[2][col] != FREE_LABEL:
                    return True

            # Check diagonals for winning condition
            if board[0][0] == board[1][1] == board[2][2] != FREE_LABEL:
                return True
            if board[0][2] == board[1][1] == board[2][0] != FREE_LABEL:
                return True
            
            full_board = np.all(board != FREE_LABEL)
            if full_board:
                return True

            # If no winner and not full_board, return False
            return False

        gm.set_endgame(tic_tac_toe_endgame)

        # Set rules
        gm.action_is_violation_if(lambda who, where, what, game: not game.started and game.agents[who][1] != 'starter', rule_description="This is not the starting player and this is the first turn.")
        gm.action_is_violation_if(lambda who, where, what, game: game.started and who == game.actions[-1]['who'], rule_description="Players cannot play two times consecutively")
        gm.action_is_violation_if(lambda who, where, what, game: where != FREE_LABEL, "board", rule_description="The space needs to be free to put a sign on it.")
        gm.action_is_violation_if(lambda who, where, what, game: game.agents[who][0] != what, rule_description="Agents can only put their own sign.")

        return gm
    
    def act(self, action) -> None:
        player = action['who']
        coordinates = action['where']

        if player == 0:
            sign = 'X'
        elif player == 1:
            sign = 'O'
        else:
            raise ValueError("Player variable has to be 0 or 1")

        return_broken_rule_string = self.interface_mode == 'gradio'
        action_dict, broken_rule_string = self.model.action("board", player, coordinates, sign, return_broken_rule_string=return_broken_rule_string)
        if broken_rule_string:
            raise ValueError(broken_rule_string)
    
    def winner(self):
        if np.all(self.model.action_spaces["board"] != FREE_LABEL):
            return None
        else:
            return self.model.actions[-1]['who']
    
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