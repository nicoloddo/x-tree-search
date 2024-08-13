from typing import Dict

class MinMaxNode:
    """
    A wrapper for nodes in the game tree for use with the MinMax algorithm.
    
    Attributes:
        node (object): The original node from the game tree.
        score (float): The score assigned to the node by the MinMax algorithm.
    """
    def __init__(self, node):
        self.node = node
        self.score = None
    
    @property
    def is_leaf(self):
        return self.node.is_leaf
    
    @property
    def children(self):
        return [MinMaxNode(child) for child in self.node.children]
    
    @property
    def id(self):
        return self.node.id

    def has_score(self):
        return self.score is not None


class MinMax:
    """
    Implements the MinMax algorithm to determine the optimal child of a node.

    Attributes:
        scoring_function (callable): A function that takes a node state and returns a numerical score.
    """
    def __init__(self, game_tree, scoring_function):
        self.gmt = game_tree
        self.score = scoring_function
    
    def run(self, node_id, *, depth=3, with_constraints: Dict = None):
        self.gmt.expand_node(node_id, depth=depth, with_constraints=with_constraints) # constrain the who for example
        root_node = MinMaxNode(self.gmt.root)
        best_child, best_value = self.minmax(root_node, True)
        return best_child, best_value
    
    def minmax(self, node, is_maximizing):
        # If the node is a leaf, return its score
        if node.is_leaf:
            node.score = self.score(node.node)
            return node.id, node.score
        
        # Initialize best value
        if is_maximizing:
            best_value = float('-inf')
        else:
            best_value = float('inf')
        
        best_child = None

        for child in node.children:
            # If child does not have a score, recursively call minmax on the child
            if not child.has_score():
                _, child_value = self.minmax(child, not is_maximizing)
                child.score = child_value
            else:
                child_value = child.score

            # Update the best value and best move depending on the player
            if is_maximizing:
                if child_value > best_value:
                    best_value = child_value
                    best_child = child.id
            else:
                if child_value < best_value:
                    best_value = child_value
                    best_child = child.id
        
        # Assign the best value to the current node
        node.score = best_value
        return best_child, best_value
