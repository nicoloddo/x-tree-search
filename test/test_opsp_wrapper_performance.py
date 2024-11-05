from algorithms.minimax_openspiel_wrapper import MiniMax, StateActionTracker
from games.breakthrough import BreakthroughOpSp as Game
import time
import pyspiel
from open_spiel.python.algorithms import minimax
import cProfile
import pstats
from pstats import SortKey

def value_function(node):
    """
    Evaluate the Breakthrough board state from black's perspective.
    A positive score means black is winning, negative means white is winning.
    
    Args:
        state: A pyspiel.State object for Breakthrough
    
    Returns:
        float: The evaluation score where:
            - Positive scores indicate black advantage
            - Negative scores indicate white advantage
    """
    if type(node) is pyspiel.State:
        state = node
    else:
        state = node.state
    depth = 0

    # Check for terminal states first
    if state.is_terminal():
        if state.returns()[0] > 0:  # Black wins (player 0)
            score = 1000 - depth  # Prefer quicker wins
        elif state.returns()[0] < 0:  # White wins (player 1)
            score = -1000 - depth  # Prefer longer losses
        return float(score)/1000.0

    # Convert state to string and count pieces
    board_str = str(state)
    black_pieces = board_str.count('b')
    white_pieces = board_str.count('w')

    # Basic material score (piece difference)
    material_score = black_pieces - white_pieces # Max= 16-1=15

    # Position scoring: reward advancement
    rows = board_str.split('\n')[:-2]  # Remove last two lines (column labels)
    position_score = 0
    board_size = len(rows)
    
    for row_idx, row in enumerate(rows):
        # Black pieces are worth more as they advance (multiply by row number from bottom)
        black_in_row = row.count('b')
        position_score += black_in_row * (row_idx + 1) # Max= 16x8=128
        
        # White pieces are worth more as they advance (multiply by row number from top)
        white_in_row = row.count('w')
        position_score -= white_in_row * (board_size - row_idx)

    # Combine scores with weights
    final_score = (material_score * 10) + position_score - depth

    return float(final_score)/1000.0

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

# Profile the wrapped explainable implementation
explainable_profiler = cProfile.Profile()
explainable_profiler.enable()
game_score, x_action = minimax.alpha_beta_search(
    game, xstate, value_function, 
    maximum_depth=max_depth, 
    maximizing_player_id=0)
explainable_profiler.disable()

x_time = time.time() - start_time

# Time the original minimax implementation
og_state = game.new_initial_state()
if pre_moves:
    og_state.apply_action(98)
    og_state.apply_action(584)

minimax._alpha_beta = minimax._alpha_beta._original_func

start_time = time.time()

# Profile the original implementation
original_profiler = cProfile.Profile()
original_profiler.enable()
original_score, original_action = minimax.alpha_beta_search(
    game, og_state, value_function,
    maximum_depth=max_depth,
    maximizing_player_id=0
)
original_profiler.disable()

original_time = time.time() - start_time

# Print comparison
print(f"\nYour MiniMax time: {x_time:.3f} seconds")
print(f"Original MiniMax time: {original_time:.3f} seconds")
print(f"Explainable action: {x_action}")
print(f"Original action: {original_action}")
print(f"Time ratio (explainable/original): {(x_time/original_time*100):.2f}%")

# Print detailed profiling information
print("\nExplainable Implementation Profile:")
explainable_stats = pstats.Stats(explainable_profiler).sort_stats(SortKey.CUMULATIVE)
explainable_stats.print_stats(20)  # Show top 20 time-consuming functions

print("\nOriginal Implementation Profile:")
original_stats = pstats.Stats(original_profiler).sort_stats(SortKey.CUMULATIVE)
original_stats.print_stats(20)