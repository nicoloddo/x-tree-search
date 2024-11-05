from algorithms.minimax_openspiel_wrapper import MiniMax
from games.breakthrough import simple_depth_dependant_scoring_function as value_function
from games.breakthrough import BreakthroughOpSp as Game

import pyspiel

game = pyspiel.load_game("breakthrough")
state = game.new_initial_state()
algorithm = MiniMax(value_function, max_depth=5)
MiniMax.set_game_state_translator(Game.state_translator)

game_score, action = algorithm.run(game, state, 0)
state.apply_action(action)
print(state)