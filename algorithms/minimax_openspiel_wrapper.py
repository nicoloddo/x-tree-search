from functools import wraps
from typing import List, Tuple, Any, Dict

class StateActionTracker:
    def __init__(self, start_with_maximizing):
        self.root = None
        self.nodes = {}
        self.start_with_maximizing = start_with_maximizing

    def set_root(self, node):
        self.root = node

    def track(self, func):
        """Convenience method to apply the tracking decorator"""
        return track_state_actions(self)(func)

class TreeNode:
    score_readability_multiplier = 1000

    @classmethod
    def game_state_translator(cls, opsp_state):
        return opsp_state

    def __init__(self, state, parent_node, maximizing_player_turn):
        self.id = ""
        self.state = state
        self.parent = parent_node
        self.children = []

        self.score = None
        self.depth = None
        self.alpha = None
        self.beta = None

        self.maximizing_player_turn = maximizing_player_turn
        self.parent_state = self.game_state_translator(self.parent.state) if self.parent is not None else None

    @property
    def is_leaf(self):
        return self.is_terminal() or self.max_search_depth_reached

    @property
    def final_node(self):
        return self.is_terminal()

    @property
    def max_search_depth_reached(self):
        if self.depth is None:
            return False
        return self.depth == 0

    @property
    def readable_score(self):
        return self.score*TreeNode.score_readability_multiplier

    @property
    def has_score(self):
        return self.score is not None

    @property 
    def fully_searched(self):
        return all([child.has_score for child in self.children])

    @property
    def score_child(self):
        if len(self.children) == 0:
            return None
        scored_children = [child for child in self.children if child.has_score]
        if not scored_children:
            return None
        if self.maximizing_player_turn:
            return max(scored_children, key=lambda child: child.score)
        else:
            return min(scored_children, key=lambda child: child.score)

    @property
    def id_length(self):
        return len(self.id)
    
    @property
    def last_move_id(self):
        return self.id[-1]
    
    @property
    def game_state(self):
        return self.game_state_translator(self.state)
    
    @property
    def game_tree_node_string(self):
        if self.parent is None:
            return "this is the root"
        return self.action_to_string(self.parent.current_player(), self.history()[-1])

    def __str__(self) -> str:
        return '\n' + f"{str(self.game_state)} {str(self.game_tree_node_string)}, id={self.id}" + ''
    
    def __getattr__(self, name):
        return getattr(self.state, name)
    
    def clone(self):
        # Wrap the cloned state in a new StateWrapper
        new_state = TreeNode(self.state.clone(), parent_node=self, maximizing_player_turn=not self.maximizing_player_turn)
        self.children.append(new_state)
        return new_state
    
    def __call__(self, *args, **kwargs):
        return self.state(*args, **kwargs)
    
    # Add representation methods
    def __repr__(self):
        return repr(self.state)
    
    # Add comparison methods
    def __eq__(self, other):
        if isinstance(other, TreeNode):
            return self.state == other.state
        return self.state == other
    
    def __hash__(self):
        return hash(self.state)

def track_state_actions(tracker: StateActionTracker):
    """
    Decorator that tracks state-action pairs during alpha-beta search in a tree structure.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state, depth, alpha, beta, value_function, maximizing_player_id):
            if tracker.root is None:
                # The other TreeNodes are instantiated when state.clone is called
                node = TreeNode(state, None, tracker.start_with_maximizing)
                node.id = '0'
                tracker.set_root(node)
            else:
                node = state
                node.id = node.parent.id + '_' + str(node.history()[-1])
            
            tracker.nodes[node.id] = node
            
            value, best_action = func(node, depth, alpha, beta, value_function, maximizing_player_id)
            node.score = value
            node.depth = depth
            node.alpha = alpha
            node.beta = beta
            
            return value, best_action

        return wrapper
    return decorator

class MiniMax:
    def __init__(self, score_function=None, *, max_depth=3, start_with_maximizing=True):
        self.score_function = score_function
        self.max_depth = max_depth
        self.start_with_maximizing = start_with_maximizing
        self.last_choice = None

        from open_spiel.python.algorithms import minimax
        self.minimax = minimax
        self.t = StateActionTracker(self.start_with_maximizing)
        self.minimax._alpha_beta = self.t.track(self.minimax._alpha_beta)
    
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
        self.t.__init__(self.start_with_maximizing)
        
        if max_depth is None:
            max_depth = self.max_depth
        
        if self.start_with_maximizing:
            maximizing_player_id = running_player_id
        else:
            maximizing_player_id = abs(running_player_id - 1) # 0 if player 1, 1 if player 0: the other player

        game_score, action = self.minimax.alpha_beta_search(game, state, self.score_function, maximum_depth=max_depth, maximizing_player_id=maximizing_player_id)

        self.last_choice = self.nodes[self.t.root.id + '_' + str(action)]
        return game_score, action
