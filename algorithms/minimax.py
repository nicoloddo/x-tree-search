from typing import Dict

class MiniMaxNode:
    """
    A wrapper for nodes in the game tree for use with the MiniMax algorithm.
    
    Attributes:
        node (object): The original node from the game tree.
        score (float): The score assigned to the node by the MiniMax algorithm.
        nodes_holder (list): Pointer to the structure that holds all the nodes in the tree.
    """
    def __init__(self, node, parent=None, nodes_holder = {}):
        self.node = node
        self.parent = parent

        self.nodes_holder = nodes_holder
        self.nodes_holder[self.id] = self

        self.score = None
        self.fully_searched = None

        self.alpha = None
        self.beta = None

        self.maximizing_player_turn = None
        self.score_child = None

        self.children = []

    def expand(self, with_constraints=None):
        # Expands the node by one depth.
        self.node.expand(with_constraints)
        self.children = self.populate_children()
    
    def populate_children(self):
        return [MiniMaxNode(child, self, self.nodes_holder) for child in self.node.children]
    
    @property
    def is_leaf(self):
        return self.node.is_leaf
    
    @property
    def id(self):
        return self.node.id
    
    @property
    def action(self):
        return self.node.action

    @property
    def has_score(self):
        return self.score is not None
    
    def __str__(self) -> str:
        return '{' + f"{str(self.node)}, id={self.node.id}" + '}'


class MiniMax:
    """
    Implements the MiniMax algorithm with optional Alpha-Beta pruning to determine the optimal child of a node.

    Attributes:
        scoring_function (callable): A function that takes a node state and returns a numerical score.
        use_alpha_beta (bool): Whether to use alpha-beta pruning.
    """
    def __init__(self, scoring_function, *, max_depth=3, start_with_maximizing=True, use_alpha_beta=True):
        self.score = scoring_function
        self.max_depth=max_depth
        self.last_choice = None
        self.search_root = None
        self.search_root_final = None
        self.nodes = {} # Holds the nodes with as key their node.node.id
        self.start_with_maximizing = start_with_maximizing

        if use_alpha_beta:
            self.algorithm = self.alphabeta
        else:
            self.algorithm = self.minimax
    
    def run(self, state_node, *, max_depth = None, expansion_constraints_self : Dict = None, expansion_constraints_other : Dict = None):
        if max_depth is None:
            max_depth = self.max_depth

        self.search_root = MiniMaxNode(state_node)
        self.nodes = self.search_root.nodes_holder

        best_child, best_value = self.algorithm(self.search_root, self.start_with_maximizing, max_depth=max_depth, constraints_maximizer=expansion_constraints_self, constraints_minimizer=expansion_constraints_other)

        if best_child is not None:
            self.search_root_final = best_child.parent
            self.last_choice = best_child
        return best_child, best_value
    
    def minimax(self, node, is_maximizing, current_depth = 0, *, max_depth, constraints_maximizer=None, constraints_minimizer=None):
        node.maximizing_player_turn = is_maximizing
        if current_depth >= max_depth:
            node.score = self.score(node.node)
            return None, None
        else:
            with_constraints = constraints_maximizer if is_maximizing else constraints_minimizer
            node.expand(with_constraints)

        # If the node is a leaf, or if we reached the max search depth, return its score
        if node.is_leaf:
            node.score = self.score(node.node)
            return None, None
        
        # Initialize best value
        if is_maximizing:
            best_value = float('-inf')
        else:
            best_value = float('inf')
        
        best_child = None

        for child in node.children:
            # If child does not have a score, recursively call minimax on the child
            if not child.has_score:
                _, _ = self.minimax(child, not is_maximizing, current_depth + 1, max_depth=max_depth, constraints_maximizer=constraints_maximizer, constraints_minimizer=constraints_minimizer)

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

    def alphabeta(self, node, is_maximizing, current_depth = 0, alpha = None, beta = None, *, max_depth, constraints_maximizer=None, constraints_minimizer=None):
        node.maximizing_player_turn = is_maximizing

        if alpha is None:
            node.alpha = None
            alpha = float('-inf')
        else:
            node.alpha = alpha
            alpha = alpha.score

        if beta is None:
            node.beta = None
            beta = float('inf')
        else:
            node.beta = beta
            beta = beta.score

        if current_depth >= max_depth:
            node.score = self.score(node.node)
            return None, None
        else:
            with_constraints = constraints_maximizer if is_maximizing else constraints_minimizer
            node.expand(with_constraints)

        # If the node is a leaf, or if we reached the max search depth, return its score
        if node.is_leaf:
            node.score = self.score(node.node)
            node.fully_searched = True
            return None, None
        
        # Initialize best value
        if is_maximizing:
            best_value = float('-inf')
        else:
            best_value = float('inf')
        
        best_child = None
        for i, child in enumerate(node.children):
            # If child does not have a score, recursively call minimax on the child
            if not child.has_score:
                _, _ = self.alphabeta(child, not is_maximizing, current_depth + 1, node.alpha, node.beta, max_depth=max_depth, constraints_maximizer=constraints_maximizer, constraints_minimizer=constraints_minimizer)

            # Update the best value and best move depending on the player
            if is_maximizing: # Maximizing player turn
                if child.score > best_value:
                    best_value = child.score
                    best_child = child

                if best_value > alpha:
                    # The maximizer will choose this score or,
                    # if there are better childs, even more.
                    # The backpropagated score will be alpha or more:
                    # at least alpha.
                    alpha = best_value
                    node.alpha = child

                # Alpha-beta pruning
                if beta <= alpha:
                    # the minimizing player had a better move to choose:
                    # because the score backpropagated from this branch will be at least alpha,
                    # and the minimizer had another branch in which the score was beta,
                    # and beta <= alpha (better for the minimizer),
                    # the minimizer will not go down this way.
                    node.fully_searched = False
                    break

            else: # Minimizer player turn
                if child.score < best_value:
                    best_value = child.score
                    best_child = child
                
                if best_value < beta:
                    # The minimizer will choose this score or,
                    # if there are worse childs, even less.
                    # The backpropagated score will be beta or less:
                    # at maximum beta.
                    beta = best_value
                    node.beta = child

                # Alpha-beta pruning
                if beta <= alpha:
                    # the minimizing player had a better move to choose:
                    # because the score backpropagated from this branch will be at maximum beta,
                    # and the maximizer had another branch in which the score was alpha,
                    # and alpha >= beta (better for the maximizer),
                    # the maximizer will not go down this way.
                    node.fully_searched = False
                    break
        
        if i+1 == len(node.children):
            node.fully_searched = True
        
        # Assign the best value to the current node
        node.score_child = best_child
        node.score = best_value

        return best_child, best_value
    
    def get_node(self, node_id: str):
        return self.nodes[node_id]
    
    def print_tree(self, node = None, level=0, is_score_child=False):
        if node is None:
            node = self.search_root_final

        indent = "  " * 2*level
        score_indicator = "*" if is_score_child else ""
        maximizer_string = "maximizer" if node.maximizing_player_turn else "minimizer"
        
        leaf_string = "leaf" if node.is_leaf else " "
        
        fully_searched_string = "fully searched" if node.fully_searched else "pruned"
        
        if node.alpha is None:
            alpha_string =  "None"
        else:
            alpha_string = node.alpha.id
        
        if node.beta is None:
            beta_string = "None"
        else:
            beta_string = node.beta.id

        print(f"{indent}{score_indicator}Node {node.id}: Score = {node.score} Alpha = {alpha_string} Beta = {beta_string} ({maximizer_string}, {fully_searched_string}) ({leaf_string})")
        
        for child in node.children:
            self.print_tree(child, level + 1, child == node.score_child)