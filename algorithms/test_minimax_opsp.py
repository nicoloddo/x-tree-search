import pyspiel
from open_spiel.python.algorithms import minimax
from algorithms.minimax_openspiel_wrapper import StateActionTracker 

t = StateActionTracker()
minimax._alpha_beta = t.track(minimax._alpha_beta)

tic_tac_toe = pyspiel.load_game("tic_tac_toe")
state = tic_tac_toe.new_initial_state()

game_score, action = minimax.alpha_beta_search(tic_tac_toe, state=state)
state.apply_action(action)
print(state)