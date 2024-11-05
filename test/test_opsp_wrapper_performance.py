from algorithms.minimax_openspiel_wrapper import MiniMax, StateActionTracker
from games.breakthrough import BreakthroughOpSp as Game
import numpy as np
import time
import pyspiel
from open_spiel.python.algorithms import minimax
import cProfile
import pstats
from pstats import SortKey
import matplotlib.pyplot as plt
import seaborn as sns


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

def run_comparison(max_depth, value_multiplier=1, pre_moves_count=2, scenario_type='depth'):
    """
    Run comparison with different parameters to test overhead.
    
    Args:
        max_depth: Maximum depth for minimax search
        value_multiplier: Multiplier for value_function computation (simulates more complex evaluation)
        pre_moves_count: Number of pre-moves to apply (increases branching)
    """
    def modified_value_function(node):
        # Run the original value function multiple times to simulate more computation
        base_value = value_function(node)
        for _ in range(value_multiplier - 1):
            _ = value_function(node)
        return base_value

    game = pyspiel.load_game("breakthrough")
    
    # Setup states
    xstate = game.new_initial_state()
    og_state = game.new_initial_state()
    
    # Apply pre-moves if specified
    for _ in range(pre_moves_count):
        if not xstate.is_terminal():
            action = xstate.legal_actions()[0]
            xstate.apply_action(action)
            og_state.apply_action(action)

    # Setup explainable version
    tracker = StateActionTracker(start_with_maximizing=True)
    if hasattr(minimax._alpha_beta, '_original_func'):
        original_func = minimax._alpha_beta._original_func
    else:
        original_func = minimax._alpha_beta
    minimax._alpha_beta = tracker.track(original_func)
    minimax._alpha_beta._original_func = original_func

    # Time explainable version
    start_time = time.time()
    game_score, x_action = minimax.alpha_beta_search(
        game, xstate, modified_value_function, 
        maximum_depth=max_depth, 
        maximizing_player_id=0)
    x_time = time.time() - start_time

    # Reset to original version
    minimax._alpha_beta = minimax._alpha_beta._original_func

    # Time original version
    start_time = time.time()
    original_score, original_action = minimax.alpha_beta_search(
        game, og_state, modified_value_function,
        maximum_depth=max_depth,
        maximizing_player_id=0
    )
    original_time = time.time() - start_time

    return {
        'scenario_type': scenario_type,
        'depth': max_depth,
        'pre_moves': pre_moves_count,
        'value_complexity': value_multiplier,
        'explainable_time': x_time,
        'original_time': original_time,
        'overhead_ratio': x_time/original_time,
        'absolute_overhead': x_time - original_time,
        'actions_match': x_action == original_action
    }

# Test different scenarios
scenarios = [
    # Test depth impact
    {'scenario_type': 'depth', 'max_depth': 4, 'value_multiplier': 1, 'pre_moves_count': 2},
    {'scenario_type': 'depth', 'max_depth': 5, 'value_multiplier': 1, 'pre_moves_count': 2},
    {'scenario_type': 'depth', 'max_depth': 6, 'value_multiplier': 1, 'pre_moves_count': 2},
    {'scenario_type': 'depth', 'max_depth': 7, 'value_multiplier': 1, 'pre_moves_count': 2},
    {'scenario_type': 'depth', 'max_depth': 8, 'value_multiplier': 1, 'pre_moves_count': 2},

    # Test branching factor impact
    {'scenario_type': 'premoves', 'max_depth': 5, 'value_multiplier': 1, 'pre_moves_count': 0},
    {'scenario_type': 'premoves', 'max_depth': 5, 'value_multiplier': 1, 'pre_moves_count': 1},
    {'scenario_type': 'premoves', 'max_depth': 5, 'value_multiplier': 1, 'pre_moves_count': 2},
    {'scenario_type': 'premoves', 'max_depth': 5, 'value_multiplier': 1, 'pre_moves_count': 3},
    {'scenario_type': 'premoves', 'max_depth': 5, 'value_multiplier': 1, 'pre_moves_count': 4},

    # Test evaluation complexity impact
    {'scenario_type': 'complexity', 'max_depth': 5, 'value_multiplier': 2, 'pre_moves_count': 2},
    {'scenario_type': 'complexity', 'max_depth': 5, 'value_multiplier': 5, 'pre_moves_count': 2},
    {'scenario_type': 'complexity', 'max_depth': 5, 'value_multiplier': 10, 'pre_moves_count': 2},
    {'scenario_type': 'complexity', 'max_depth': 5, 'value_multiplier': 15, 'pre_moves_count': 2},
    {'scenario_type': 'complexity', 'max_depth': 5, 'value_multiplier': 20, 'pre_moves_count': 2},
]

def plot_results(results):
    plt.style.use('default')
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(15, 18))
    
    # 1. Depth vs Times
    depth_results = sorted(
        [r for r in results if r['scenario_type'] == 'depth'],
        key=lambda x: x['depth']
    )
    depths = [r['depth'] for r in depth_results]
    ax1.plot(depths, [r['explainable_time'] for r in depth_results], 'b-o', label='Explainable')
    ax1.plot(depths, [r['original_time'] for r in depth_results], 'r-o', label='Original')
    ax1.set_title('Search Depth vs Execution Time')
    ax1.set_xlabel('Search Depth')
    ax1.set_ylabel('Time (seconds)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Depth vs Overhead Ratio
    ax2.plot(depths, [r['overhead_ratio'] for r in depth_results], 'g-o')
    ax2.set_title('Search Depth vs Overhead Ratio')
    ax2.set_xlabel('Search Depth')
    ax2.set_ylabel('Overhead Ratio (explainable/original)')
    ax2.axhline(y=1, color='r', linestyle='--', alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    # 3. Value Complexity vs Times
    complexity_results = sorted(
        [r for r in results if r['scenario_type'] == 'complexity'],
        key=lambda x: x['value_complexity']
    )
    complexities = [r['value_complexity'] for r in complexity_results]
    ax3.plot(complexities, [r['explainable_time'] for r in complexity_results], 'b-o', label='Explainable')
    ax3.plot(complexities, [r['original_time'] for r in complexity_results], 'r-o', label='Original')
    ax3.set_title('Evaluation Complexity vs Execution Time')
    ax3.set_xlabel('Value Function Complexity (multiplier)')
    ax3.set_ylabel('Time (seconds)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Value Complexity vs Overhead Ratio
    ax4.plot(complexities, [r['overhead_ratio'] for r in complexity_results], 'g-o')
    ax4.set_title('Evaluation Complexity vs Overhead Ratio')
    ax4.set_xlabel('Value Function Complexity (multiplier)')
    ax4.set_ylabel('Overhead Ratio (explainable/original)')
    ax4.axhline(y=1, color='r', linestyle='--', alpha=0.3)
    ax4.grid(True, alpha=0.3)

    # 5. Pre-moves vs Times
    premoves_results = sorted(
        [r for r in results if r['scenario_type'] == 'premoves'],
        key=lambda x: x['pre_moves']
    )
    premoves = [r['pre_moves'] for r in premoves_results]
    ax5.plot(premoves, [r['explainable_time'] for r in premoves_results], 'b-o', label='Explainable')
    ax5.plot(premoves, [r['original_time'] for r in premoves_results], 'r-o', label='Original')
    ax5.set_title('Pre-moves vs Execution Time')
    ax5.set_xlabel('Number of Pre-moves')
    ax5.set_ylabel('Time (seconds)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # 6. Pre-moves vs Overhead Ratio
    ax6.plot(premoves, [r['overhead_ratio'] for r in premoves_results], 'g-o')
    ax6.set_title('Pre-moves vs Overhead Ratio')
    ax6.set_xlabel('Number of Pre-moves')
    ax6.set_ylabel('Overhead Ratio (explainable/original)')
    ax6.axhline(y=1, color='r', linestyle='--', alpha=0.3)
    ax6.grid(True, alpha=0.3)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('./test/performance_output/minimax_performance_analysis.png')
    plt.close()

    # Create additional plot for absolute overhead
    plt.figure(figsize=(10, 6))
    plt.plot(depths, [r['absolute_overhead'] for r in depth_results], 'b-o', label='By Depth')
    plt.plot(complexities, [r['absolute_overhead'] for r in complexity_results], 'r-o', label='By Complexity')
    plt.plot(premoves, [r['absolute_overhead'] for r in premoves_results], 'g-o', label='By Pre-moves')
    plt.title('Absolute Overhead Analysis')
    plt.xlabel('Parameter Value (Depth/Complexity/Pre-moves)')
    plt.ylabel('Absolute Overhead (seconds)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('./test/performance_output/minimax_absolute_overhead.png')
    plt.close()

results = []
for scenario in scenarios:
    result = run_comparison(**scenario)
    results.append(result)
    print(f"\nScenario: {scenario}")
    print(f"Explainable time: {result['explainable_time']:.3f}s")
    print(f"Original time: {result['original_time']:.3f}s")
    print(f"Overhead ratio: {result['overhead_ratio']:.2f}x")
    print(f"Absolute overhead: {result['absolute_overhead']:.3f}s")
    print(f"Actions match: {result['actions_match']}")

# Analyze results
print("\nAnalysis:")
print(f"Average overhead ratio: {sum(r['overhead_ratio'] for r in results)/len(results):.2f}x")
print(f"Average absolute overhead: {sum(r['absolute_overhead'] for r in results)/len(results):.3f}s")
print(f"Std dev of absolute overhead: {(sum((r['absolute_overhead'] - sum(r['absolute_overhead'] for r in results)/len(results))**2 for r in results)/len(results))**0.5:.3f}s")

# Plot
plot_results(results)