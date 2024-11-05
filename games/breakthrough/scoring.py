import numpy as np

def simple_depth_dependant_scoring_function(node):
    """Evaluate the Breakthrough board state from the perspective of the 'b' (black) player"""
    state = node.game_state
    depth = node.depth
    score = 0

    # Check for winning condition
    game_ended = False
    if np.any(state[-1] == 'b'):
        score += 1000 - depth  # Black wins
        game_ended = True
    if np.any(state[0] == 'w'):
        score -= 1000 + depth  # White wins
        game_ended = True
    
    if game_ended:
        return float(score)/1000.0

    # Count pieces for each player
    black_pieces = np.sum(state == 'b')
    white_pieces = np.sum(state == 'w')
    
    # Piece advantage
    score += (black_pieces - white_pieces) * 10

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

    return float(score)/1000.0

def simple_depth_dependant_scoring_function_opsp(node):
    """
    Evaluate the Breakthrough board state from black's perspective.
    A positive score means black is winning, negative means white is winning.
    
    Args:
        state: A pyspiel.State object for Breakthrough
        depth: Current depth in the game tree
    
    Returns:
        float: The evaluation score where:
            - Positive scores indicate black advantage
            - Negative scores indicate white advantage
            - For terminal states:
                * Wins are preferred sooner (1000 - depth)
                * Losses are preferred later (-1000 - depth)
    """
    state = node.state
    depth = node.depth

    # Check for terminal states first
    if state.is_terminal():
        if state.returns()[0] > 0:  # Black wins (player 0)
            score = 1000 + depth  # Prefer quicker wins (depth is higher for quicker wins)
        elif state.returns()[0] < 0:  # White wins (player 1)
            score = -1000 + depth  # Prefer longer losses (depth is lower for longer losses)
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
    final_score = (material_score * 10) + position_score + depth

    return float(final_score)/1000.0