from algorithms.minimax_openspiel_wrapper import MiniMax, StateActionTracker
from games.breakthrough import simple_depth_dependant_scoring_function as value_function
from games.breakthrough import BreakthroughOpSp as Game
import time
import pyspiel
from open_spiel.python.algorithms import minimax

game = pyspiel.load_game("breakthrough")
max_depth = 6
pre_moves = True

# Time the wrapped explainable implementation
xstate = game.new_initial_state()
if pre_moves:
    xstate.apply_action(98)
    xstate.apply_action(584)

tracker = StateActionTracker(start_with_maximizing=True)
MiniMax.set_game_state_translator(Game.state_translator)

# If already wrapped, get the original function
if hasattr(minimax._alpha_beta, '_original_func'):
    original_func = minimax._alpha_beta._original_func
    print("Already wrapped!")
else:
    original_func = minimax._alpha_beta
# Apply new wrapper
minimax._alpha_beta = tracker.track(original_func)
# Store reference to original function
minimax._alpha_beta._original_func = original_func

start_time = time.time()
game_score, x_action = minimax.alpha_beta_search(
    game, xstate, value_function, 
    maximum_depth=max_depth, 
    maximizing_player_id=0)
x_time = time.time() - start_time

# Time the original minimax implementation
og_state = game.new_initial_state()
if pre_moves:
    og_state.apply_action(98)
    og_state.apply_action(584)

minimax._alpha_beta = minimax._alpha_beta._original_func

# Time original minimax
start_time = time.time()
original_score, original_action = minimax.alpha_beta_search(
    game, og_state, value_function,
    maximum_depth=max_depth,
    maximizing_player_id=0
)
original_time = time.time() - start_time

# Print comparison
print(f"\nYour MiniMax time: {x_time:.3f} seconds")
print(f"Original MiniMax time: {original_time:.3f} seconds")
print(f"Explainable action: {x_action}")
print(f"Original action: {original_action}")
print(f"Time ratio (explainable/original): {(x_time/original_time*100):.2f}%")