class Minimax:
    """
    Implements the Minimax algorithm to determine the optimal move for a player.

    Attributes:
        scoring_function (callable): A function that takes a game state and returns a numerical score.
    """
    def __init__(self, game_tree, scoring_function):
        self.gmt = game_tree
        self.score = scoring_function
    
    def start(self):
        self.minimax(self.gmt.root)




        


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

        self.gmt.expand_node(node.id)
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

    def get_best_move(self, root, depth):
        """
        Determines the best move from the root node.

        Args:
            root (TreeNode): The root node of the game tree.
            depth (int): The maximum depth to search in the tree.

        Returns:
            TreeNode: The child node that represents the best move.
        """
        best_value = float('-inf') if root.maximizing_player else float('inf')
        best_move = None

        for child in root.children:
            value = self.minimax(child, depth-1, not root.maximizing_player)
            if root.maximizing_player:
                if value > best_value:
                    best_value = value
                    best_move = child
            else:
                if value < best_value:
                    best_value = value
                    best_move = child

        return best_move
