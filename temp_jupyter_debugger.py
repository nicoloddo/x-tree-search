# %%
from src.game_model import GameModel

# %% [markdown]
# ## Declare environment and agents:

# %%
"""
Initializes the GameModel with a labeled environment.

Args:
    default_label (list of str): The default labels to assign to each column in the environment.
    additional_labels (list of str): Other possible labels that can be assigned to the environment elements.

    default_agents_labels (list of str)): The default labels to each row of agent features.
    additional_agents_labels (list of list of strings): For each agent feature, specify other possible labels that can be assigned to each.

    environment_dimensions (list of int): Dimensions of the environment matrix. 
    Consider adding an additional dimension to the environment for time if rules refer to previous timesteps.

    agents_dimensions (list of int): Dimensions of the agents matrix.
    Consider to use the first dimension for the number of player and the second dimension for the number of features.

    dimensions_descriptions (str): String explaining each dimension of the environment and of the agents (optional)
    game_name (str): String with the name of the game (optional)
"""

gm = GameModel( 
agents_number=2, default_agent_features=['not starter', 'X'], additional_agent_features=[['starter'], ['O']], 
agent_features_descriptions="2 players with feature 1 indicating who is starting, and feature 2 indicating their symbol.",
game_name="tic-tac-toe")
gm.add_action_space("board", dimensions=[3, 3], default_labels=['free'], additional_labels=[['X', 'O']], dimensions_descriptions="3x3 board.")

print(gm)
print()
print(gm.printable_rules)

# %%
# Let's disable actions on the agent feature space.
gm.disable_actions(on="agent")
print(gm.printable_action_spaces)

# %% [markdown]
# ## Initialize parameters

# %%
gm.agents[1, 1] = 'O'
gm.agents[1, 0] = 'starter'
print(gm.agents)

# %% [markdown]
# ## Define the dynamic to end the game

# %%
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

# %% [markdown]
# ## Define the rules

# %% [markdown]
# Define rules by specifying a conditional that is true if the rule is broken. 
# The conditional needs to be a callable function with arguments who, where, what and game.
# 
# Rules contrain a given action space by limiting the possible actions appliable.
# 
# Specify the action space that the rule applies to after the callable function (as second argument).
# If you don't specify anything, the rules are applied to all the action spaces.

# %%
"""Only the player whose starter can play the first turn:
game.agents[who] = the agent who does the action
agent[0] refers to the agent's first feature, which we assigned to the status
"""
gm.action_is_violation_if(lambda who, where, what, game: not game.started and game.agents[who][0] != 'starter', rule_description="This is not the starting player and this is the first turn.")

# %%
"""Agents need to alternate actions:
The last action was done by the same player.
"""
gm.action_is_violation_if(lambda who, where, what, game: game.started and who == game.actions[-1]['who'], rule_description="Players cannot play two times consecutively")

# %%
"""You can only put a sign if the space is free:
"""
gm.action_is_violation_if(lambda who, where, what, game: where != 'free', "board", rule_description="The space needs to be free to put a sign on it.")

# %%
"""Agents can only put their own sign:
agent[1] refers to the agent's symbol.
"""
gm.action_is_violation_if(lambda who, where, what, game: game.agents[who][1] != what, rule_description="Agents can only put their own sign.")

# %%
print(gm.printable_rules)

# %% [markdown]
# ## Example Actions:

# %%
board = gm.action_spaces["board"]

# %% [markdown]
# Action not permitted:

# %%
gm.action("board", 0, [0, 0], 'X')
board

# %% [markdown]
# Action that respects the rules:

# %%
board.available_labels

# %%
gm.action("board", 1, [0, 0], 'O')
board

# %% [markdown]
# Other actions that do not respect the rules:

# %%
gm.action("board", 1, [1, 0], 'O')
board

# %%
gm.action("board", 0, [0, 0], 'X')
board

# %%
gm.action("agent", 0, 'O', [0,0])
board

# %%
gm.action("board", 0, [2, 1], 'O')
board

# %% [markdown]
# ## Example of game:

# %% [markdown]
# It's suggested to make a wrapper definition for actions in the game:

# %%
def put_sign(player, coordinates):
    if player == 0:
        sign = 'X'
    elif player == 1:
        sign = 'O'
    else:
        raise ValueError("Player variable has to be 0 or 1")

    performed = gm.action("board", player, coordinates, sign)

    if performed:
        print(gm.action_spaces["board"])

# %%
put_sign(0, [1,1])

# %%
put_sign(0, [0,1])

# %%
put_sign(1, [2,2])

# %%
put_sign(0, [2,0])

# %%
put_sign(1, [0,2])

# %%
gm.ended

# %%
previous_board = gm.theoretical_unapply_actions(3)["board"]

# %%
previous_board

# %%
print(previous_board)

# %%
put_sign(0, [0,0])

# %%
put_sign(0, [0,1])

# %%
put_sign(1, [1,2])

# %%
gm.ended

# %%
put_sign(0, [2,1])


