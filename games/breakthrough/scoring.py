import numpy as np
from games.breakthrough.breakthrough import Breakthrough

def simple_depth_dependant_scoring_function(node):
    """Evaluate the Breakthrough board state from the perspective of the 'b' (black) player"""
    state = node.game_state
    depth = node.depth
    score = 0
    
    # Count pieces for each player
    black_pieces = np.sum(state == 'b')
    white_pieces = np.sum(state == 'w')
    
    # Piece advantage
    score += (black_pieces - white_pieces) * 10

    # Check for winning condition
    if np.any(state[-1] == 'b'):
        return score + 1000 - depth  # Black wins
    if np.any(state[0] == 'w'):
        return score - 1000 + depth  # White wins

    # Evaluate advanced positions
    rows, cols = state.shape
    for i in range(rows):
        for j in range(cols):
            if state[i, j] == 'b':
                score += i * 2  # Reward forward positions for black
            elif state[i, j] == 'w':
                score -= (rows - 1 - i) * 2  # Penalize forward positions for white

    # Adjust score based on depth
    score -= depth

    return score/1000
