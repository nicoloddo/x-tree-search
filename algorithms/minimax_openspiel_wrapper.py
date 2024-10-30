from functools import wraps
from typing import List, Tuple, Any, Dict

class TreeNode:
    def __init__(self, state, action, parent=None, node_id="0", nodes_holder=None):
        self.state = state.clone() if state else None
        self.action = action
        self.parent = parent
        self.children = []
        self.id = node_id

        self.nodes_holder = nodes_holder or {node_id: self}

    def add_child(self, state, action):
        # Clone the current state and apply the action to get the immediate next state
        child_id = f"{self.id}_{action}"
        if child_id in self.nodes_holder:
            return self.nodes_holder[child_id]

        next_state = state.clone()
        next_state.apply_action(action)
        
        child = TreeNode(next_state, action, self, child_id, self.nodes_holder)
        self.children.append(child)
        self.nodes_holder[child_id] = child

        return child

class StateActionTracker:
    def __init__(self):
        self.root = None

    def set_root(self, state):
        self.root = TreeNode(state, None)

    def track(self, func):
        """Convenience method to apply the tracking decorator"""
        return track_state_actions(self)(func)

def track_state_actions(tracker: StateActionTracker):
    """
    Decorator that tracks state-action pairs during alpha-beta search in a tree structure.
    
    Usage:
        tracker = StateActionTracker()
        
        @track_state_actions(tracker)
        def _alpha_beta(state, depth, alpha, beta, value_function, maximizing_player_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state, depth, *args, **kwargs):
            if tracker.root is None:
                tracker.set_root(state)
            
            if state.is_terminal() or depth == 0:
                current_node = tracker.root
                for action in state.history():
                    current_node = current_node.add_child(current_node.state, action)
            
            return func(state, depth, *args, **kwargs)
        return wrapper
    return decorator

from open_spiel.python.algorithms import minimax
class MiniMax:
    def __init__(self, score_function=None, *, max_depth=3, start_with_maximizing=True):
        t = StateActionTracker()
        minimax._alpha_beta = t.track(minimax._alpha_beta)

        self.score_function = score_function
        self.max_depth = max_depth
        self.start_with_maximizing = start_with_maximizing

    def run(self, game, state, running_player_id, max_depth=None):
        """
        :param game: The game to run the algorithm on.
        :param state: The state to start the search from.
        :param running_player_id: The id of the player that is running the algorithm.
        :param max_depth: The maximum depth to search to.
        """
        if max_depth is None:
            max_depth = self.max_depth
        
        if self.start_with_maximizing:
            maximizing_player_id = running_player_id
        else:
            maximizing_player_id = abs(running_player_id - 1) # 0 if player 1, 1 if player 0: the other player

        return minimax.alpha_beta_search(game, state, self.score_function, maximum_depth=max_depth, maximizing_player_id=maximizing_player_id)
