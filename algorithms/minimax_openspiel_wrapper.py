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
    
    @property
    def nodes(self):
        return self.root.nodes_holder

    def set_root(self, state):
        self.root = TreeNode(state, None)

    def track(self, func):
        """Convenience method to apply the tracking decorator"""
        return track_state_actions(self)(func)

class StateWrapper:
    def __init__(self, state, alpha=None, beta=None):
        self.state = state
        self.children = []
        self.alpha = alpha
        self.beta = beta
    
    def __getattr__(self, name):
        return getattr(self.state, name)
    
    def clone(self):
        # Wrap the cloned state in a new StateWrapper
        new_state = StateWrapper(self.state.clone())
        self.children.append(new_state)
        return new_state
    
    def __call__(self, *args, **kwargs):
        return self.state(*args, **kwargs)
    
        # Add representation methods
    def __repr__(self):
        return repr(self.state)
    
    def __str__(self):
        return str(self.state)
    
    # Add comparison methods
    def __eq__(self, other):
        if isinstance(other, StateWrapper):
            return self.state == other.state
        return self.state == other
    
    def __hash__(self):
        return hash(self.state)
    
    # Add iterator support if the state is iterable
    def __iter__(self):
        return iter(self.state)
    
    # Add length support if the state supports len()
    def __len__(self):
        return len(self.state)

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
        def wrapper(state, depth, alpha, beta, value_function, maximizing_player_id):
            state = StateWrapper(state, alpha, beta)
            if tracker.root is None:
                tracker.set_root(state)
            
            """
            if state.is_terminal() or depth == 0:
                current_node = tracker.root
                history = state.history()[len(tracker.root.state.history()):]
                for action in history:
                    current_node = current_node.add_child(current_node.state, action)
            """
            
            return func(state, depth, alpha, beta, value_function, maximizing_player_id)
        return wrapper
    return decorator

from open_spiel.python.algorithms import minimax
class MiniMax:
    def __init__(self, score_function=None, *, max_depth=3, start_with_maximizing=True):
        self.score_function = score_function
        self.max_depth = max_depth
        self.start_with_maximizing = start_with_maximizing
        self.last_choice = None
    
    @property
    def nodes(self):
        return self.t.nodes

    def run(self, game, state, running_player_id, max_depth=None):
        """
        :param game: The game to run the algorithm on.
        :param state: The state to start the search from.
        :param running_player_id: The id of the player that is running the algorithm.
        :param max_depth: The maximum depth to search to.
        """
        self.t = StateActionTracker()
        minimax._alpha_beta = self.t.track(minimax._alpha_beta)

        if max_depth is None:
            max_depth = self.max_depth
        
        if self.start_with_maximizing:
            maximizing_player_id = running_player_id
        else:
            maximizing_player_id = abs(running_player_id - 1) # 0 if player 1, 1 if player 0: the other player

        game_score, action = minimax.alpha_beta_search(game, state, self.score_function, maximum_depth=max_depth, maximizing_player_id=maximizing_player_id)

        self.last_choice = self.nodes[self.t.root.id + '_' + str(action)]
        return game_score, action
