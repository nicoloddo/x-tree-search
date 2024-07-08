from absl.testing import absltest
from open_spiel.python import rl_environment
from open_spiel.python.algorithms import mcts
from open_spiel.python.algorithms import mcts_agent

from absl import app
from absl import flags
from absl import logging

import pyspiel
from open_spiel.python.visualizations import treeviz

GAME = "tic_tac_toe"
VERBOSE = True
OUTPUT = "./results/treeviz.svg"

game = pyspiel.load_game(GAME)
game_type = game.get_type()

def _zero_sum_node_decorator(state):
  """Custom node decorator that only shows the return of the first player."""
  attrs = treeviz.default_node_decorator(state)  # get default attributes
  if state.is_terminal():
    attrs["label"] = str(int(state.returns()[0]))
  return attrs

if game_type.dynamics == pyspiel.GameType.Dynamics.SIMULTANEOUS:
    logging.warn("%s is not turn-based. Trying to reload game as turn-based.",
                    GAME)
    game = pyspiel.load_game_as_turn_based(GAME)
    game_type = game.get_type()

if game_type.dynamics != pyspiel.GameType.Dynamics.SEQUENTIAL:
    raise ValueError("Game must be sequential, not {}".format(
        game_type.dynamics))

if (game_type.utility == pyspiel.GameType.Utility.ZERO_SUM and
      game.num_players() == 2):
    logging.info("Game is zero-sum: only showing first-player's returns.")
    gametree = treeviz.GameTree(game, node_decorator=_zero_sum_node_decorator)
else:
    # use default decorators
    gametree = treeviz.GameTree(game)
  
env = rl_environment.Environment(game, include_full_state=True)
num_players = env.num_players
num_actions = env.action_spec()["num_actions"]

# Create the MCTS bot. Both agents can share the same bot in this case since
# there is no state kept between searches. See mcts.py for more info about
# the arguments.
mcts_bot = mcts.MCTSBot(env.game, 1.5, 100, mcts.RandomRolloutEvaluator())

agents = [
    mcts_agent.MCTSAgent(player_id=idx, num_actions=num_actions,
                            mcts_bot=mcts_bot)
    for idx in range(num_players)
]

time_step = env.reset()
while not time_step.last():
    player_id = time_step.observations["current_player"]
    agent_output = agents[player_id].step(time_step)
    time_step = env.step([agent_output.action])
for agent in agents:
    agent.step(time_step)

print("Done.")


if VERBOSE:
    logging.info("Game tree:\n%s", gametree.to_string())

    gametree.draw(OUTPUT, prog="dot")
    logging.info("Game tree saved to file: %s", OUTPUT)