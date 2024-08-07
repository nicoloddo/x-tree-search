from src.game.game_model import GameModel
from src.game.game_tree import GameTree

class TicTacToe:
    gm = GameModel( 
    agents_number=2, default_agent_features=['not starter', 'X'], additional_agent_features=[['starter'], ['O']], 
    agent_features_descriptions="2 players with feature 1 indicating who is starting, and feature 2 indicating their symbol.",
    game_name="tic-tac-toe")
    gm.add_action_space("board", dimensions=[3, 3], default_labels=['free'], additional_labels=[['X', 'O']], dimensions_descriptions="3x3 board.")

    # Disable actions on the agent feature space.
    gm.disable_actions(on="agent")
    gm.agents[1, 1] = 'O'
    gm.agents[1, 0] = 'starter'

    def tic_tac_toe_endgame(game):
        board = game.action_spaces["board"]
        # Check rows for winning condition
        for row in board:
            if row[0] == row[1] == row[2] != 'free':
                return True

        # Check columns for winning condition
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != 'free':
                return True

        # Check diagonals for winning condition
        if board[0][0] == board[1][1] == board[2][2] != 'free':
            return True
        if board[0][2] == board[1][1] == board[2][0] != 'free':
            return True

        # If no winner, return False
        return False

    gm.set_endgame(tic_tac_toe_endgame)

    gm.action_is_violation_if(lambda who, where, what, game: not game.started and game.agents[who][0] != 'starter', rule_description="This is not the starting player and this is the first turn.")
    gm.action_is_violation_if(lambda who, where, what, game: game.started and who == game.actions[-1]['who'], rule_description="Players cannot play two times consecutively")
    gm.action_is_violation_if(lambda who, where, what, game: where != 'free', "board", rule_description="The space needs to be free to put a sign on it.")
    gm.action_is_violation_if(lambda who, where, what, game: game.agents[who][1] != what, rule_description="Agents can only put their own sign.")

    gmt = GameTree(gm, "board")