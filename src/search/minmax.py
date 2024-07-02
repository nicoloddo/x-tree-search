class Minimax:
    """
    Implements the Minimax algorithm to determine the optimal move for a player.

    Attributes:
        scoring_function (callable): A function that takes a game state and returns a numerical score.
    """
    def __init__(self, scoring_function):
        self.score = scoring_function

    def minimax(self, node, depth, maximizing_player):
        """
        Recursively calculates the best score using the Minimax algorithm.

        Args:
            node (TreeNode): The current node in the game tree.
            depth (int): The maximum depth to search in the tree.
            maximizing_player (bool): True if the current move is by the maximizing player, False otherwise.

        Returns:
            int: The best score achievable from this node.
        """
        if depth == 0 or node.is_leaf:
            return self.score(node.state)

        if maximizing_player:
            value = float('-inf')
            for child in node.children:
                value = max(value, self.minimax(child, depth-1, False))
            return value
        else:
            value = float('inf')
            for child in node.children:
                value = min(value, self.minimax(child, depth-1, True))
            return value
