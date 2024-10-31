import numpy as np

def simple_scoring_function(node, depth):
    """ Evaluate the Tic Tac Toe board state for the 'X' player's perspective """
    state = node.state
    score = 0
    
    # Possible lines to check (3 rows, 3 columns, 2 diagonals)
    lines = []
    # Rows and columns
    for i in range(3):
        lines.append(state[i, :])  # Row
        lines.append(state[:, i])  # Column
    # Diagonals
    lines.append(np.array([state[i, i] for i in range(3)]))  # Main diagonal
    lines.append(np.array([state[i, 2 - i] for i in range(3)]))  # Anti-diagonal

    for line in lines:
        if np.all(line == "O"):
            score += 100  # 'X' wins
        elif np.all(line == "X"):
            score -= 100  # 'O' wins
        elif np.count_nonzero(line == "O") == 2 and np.count_nonzero(line == "free") == 1:
            score += 10  # 'X' is one move away from winning
        elif np.count_nonzero(line == "X") == 2 and np.count_nonzero(line == "free") == 1:
            score -= 10  # 'O' is one move away from winning

    return score

def simple_depth_dependant_scoring_function(node, depth):
    """ Evaluate the Tic Tac Toe board state for the 'X' player's perspective """
    state = node.state
    score = 0
    
    # Possible lines to check (3 rows, 3 columns, 2 diagonals)
    lines = []
    # Rows and columns
    for i in range(3):
        lines.append(state[i, :])  # Row
        lines.append(state[:, i])  # Column
    # Diagonals
    lines.append(np.array([state[i, i] for i in range(3)]))  # Main diagonal
    lines.append(np.array([state[i, 2 - i] for i in range(3)]))  # Anti-diagonal

    for line in lines:
        if np.all(line == "O"):
            score += 1000 - depth # 'X' wins
        elif np.all(line == "X"):
            score -= 1000 - depth # 'O' wins
        elif np.count_nonzero(line == "O") == 2 and np.count_nonzero(line == "free") == 1:
            score += 100 - depth # 'X' is one move away from winning
        elif np.count_nonzero(line == "X") == 2 and np.count_nonzero(line == "free") == 1:
            score -= 100 - depth  # 'O' is one move away from winning

    return score