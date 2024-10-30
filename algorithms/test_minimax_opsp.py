
from algorithms.minimax_openspiel_wrapper import MiniMax

import pyspiel

tic_tac_toe = pyspiel.load_game("tic_tac_toe")
state = tic_tac_toe.new_initial_state()
algorithm = MiniMax(max_depth=30)

game_score, action = algorithm.run(tic_tac_toe, state=state)
state.apply_action(action)
print(state)