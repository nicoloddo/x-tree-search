from typing import Dict

class MinMaxNode:
    """
    A wrapper for nodes in the game tree for use with the MinMax algorithm.
    
    Attributes:
        node (object): The original node from the game tree.
        score (float): The score assigned to the node by the MinMax algorithm.
    """
    def __init__(self, node, parent=None):
        self.node = node
        self.parent = parent
        self.score = None

        self.maximizing_player_turn = None
        self.score_child = None

        self.children = self.populate_children()
    
    def populate_children(self):
        return [MinMaxNode(child, self) for child in self.node.children]
    
    @property
    def is_leaf(self):
        return self.node.is_leaf
    
    @property
    def id(self):
        return self.node.id

    def has_score(self):
        return self.score is not None
    
    def __str__(self) -> str:
        return self.id


class MinMax:
    """
    Implements the MinMax algorithm with optional Alpha-Beta pruning to determine the optimal child of a node.

    Attributes:
        scoring_function (callable): A function that takes a node state and returns a numerical score.
        use_alpha_beta (bool): Whether to use alpha-beta pruning.
    """
    def __init__(self, scoring_function, *, start_with_maximizing=True, use_alpha_beta=False):
        self.score = scoring_function
        self.last_choice = None
        self.start_with_maximizing = start_with_maximizing
        self.use_alpha_beta = use_alpha_beta
    
    def run(self, game_tree, node_id, *, depth=3, with_constraints: Dict = None):
        state_node = game_tree.nodes[node_id]
        game_tree.expand_node(node_id, depth=depth, with_constraints=with_constraints) # constrain the who for example
        
        search_root = MinMaxNode(state_node)
        if len(search_root.children) > 0:
            if self.use_alpha_beta:
                best_child, best_value = self.alpha_beta(search_root, depth, float('-inf'), float('inf'), self.start_with_maximizing)
            else:
                best_child, best_value = self.minmax(search_root, self.start_with_maximizing)
            self.last_choice = best_child
            return best_child.id, best_value
        else:
            return None, None
    
    def minmax(self, node, is_maximizing):
        node.maximizing_player_turn = is_maximizing

        # If the node is a leaf, return its score
        if node.is_leaf:
            node.score = self.score(node.node)
            return node, node.score
        
        # Initialize best value
        if is_maximizing:
            best_value = float('-inf')
        else:
            best_value = float('inf')
        
        best_child = None

        for child in node.children:
            # If child does not have a score, recursively call minmax on the child
            if not child.has_score():
                _, _ = self.minmax(child, not is_maximizing)

            # Update the best value and best move depending on the player
            if is_maximizing:
                if child.score > best_value:
                    best_value = child.score
                    best_child = child
            else:
                if child.score < best_value:
                    best_value = child.score
                    best_child = child
        
        # Assign the best value to the current node
        node.score_child = best_child
        node.score = best_value
        return best_child, best_value

    def alpha_beta(self, node, depth, alpha, beta, is_maximizing):
            node.maximizing_player_turn = is_maximizing

            if depth == 0 or node.is_leaf:
                node.score = self.score(node.node)
                return node, node.score
            
            best_child = None

            if is_maximizing:
                best_value = float('-inf')
                for child in node.children:
                    if not child.has_score():
                        _, child_score = self.alpha_beta(child, depth - 1, alpha, beta, False)
                    else:
                        child_score = child.score

                    if child_score > best_value:
                        best_value = child_score
                        best_child = child
                    alpha = max(alpha, best_value)
                    if beta <= alpha:
                        break
            else:
                best_value = float('inf')
                for child in node.children:
                    if not child.has_score():
                        _, child_score = self.alpha_beta(child, depth - 1, alpha, beta, True)
                    else:
                        child_score = child.score

                    if child_score < best_value:
                        best_value = child_score
                        best_child = child
                    beta = min(beta, best_value)
                    if beta <= alpha:
                        break

            node.score_child = best_child
            node.score = best_value
            return best_child, best_value