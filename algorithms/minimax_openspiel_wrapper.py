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
    score_readability_multiplier = 1000 # scores are from 0 to 1

    @classmethod
    def game_state_translator(cls, opsp_state):
        return opsp_state

    def __init__(self, state, parent_node, maximizing_player_turn):
        self.id = ""
        self.state = state
        self.parent = parent_node
        self.maximizing_player_turn = maximizing_player_turn

        self.children = []
        self.score = None
        self._history = None
        self._depth = None
        self._translated_state = None  # Cache for translated game state
        self._parent_state = None

    @property
    def parent_state(self):
        if self._parent_state is None and self.parent is not None:
            self._parent_state = self.parent.game_state
        return self._parent_state

    @property
    def game_state(self):
        if self._translated_state is None:
            self._translated_state = self.game_state_translator(self.state)
        return self._translated_state

    def history(self):
        if self._history is None:
            self._history = self.state.history()
        return self._history
    
    @property
    def depth(self):
        if self._depth is None:
            self._depth = len(self.history())
        return self._depth

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def final_node(self):
        return self.is_terminal()

    @property
    def max_search_depth_reached(self):
        return self.is_leaf and not self.final_node

    @property
    def readable_score(self):
        return self.score*TreeNode.score_readability_multiplier

    @property
    def has_score(self):
        return self.score is not None

    @property 
    def fully_searched(self):
        return len(self.children) == len(self.legal_actions())

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
    
    def get_deep_score_child(self):
        if self.score_child is not None:
            return self.score_child.get_deep_score_child()
        else:
            return self

    @property
    def deep_score_child(self):
        return self.get_deep_score_child()
        
    @property
    def alpha(self):
        if self.maximizing_player_turn:
            return self.score_child
        else:
            return None
    
    @property
    def beta(self):
        if self.maximizing_player_turn:
            return None
        else:
            return self.score_child

    @property
    def id_length(self):
        return len(self.id)
    
    @property
    def last_move_id(self):
        return self.history()[-1]
    
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
            return self.state.serialize() == other.state.serialize()
        return self.state.serialize() == other.serialize()
    
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
            
            """ Adding this increases way too much the computation time
            for action in node.legal_actions()[len(node.children):]:
                missing_child = node.clone()
                missing_child.apply_action(action)
                tracker.nodes[node.id + '_' + str(action)] = missing_child"""
            
            return value, best_action

        return wrapper
    return decorator


import graphviz
import tempfile
from open_spiel.python.algorithms import minimax
class MiniMax:
    tree_node_class = TreeNode
    @classmethod
    def set_game_state_translator(cls, game_state_translator):
        cls.tree_node_class.game_state_translator = game_state_translator
    
    def __init__(self, score_function=None, *, max_depth=3, start_with_maximizing=True):
        self.score_function = score_function
        self.max_depth = max_depth
        self.start_with_maximizing = start_with_maximizing
        self.last_choice = None
        self.tracker = None
    
    @property
    def nodes(self):
        return self.tracker.nodes if self.tracker is not None else {}

    def run(self, game, state, running_player_id, max_depth=None):
        """
        :param game: The game to run the algorithm on.
        :param state: The state to start the search from.
        :param running_player_id: The id of the player that is running the algorithm.
        :param max_depth: The maximum depth to search to.
        """
        try:
            self.tracker = StateActionTracker(self.start_with_maximizing)

            # If already wrapped, get the original function
            if hasattr(minimax._alpha_beta, '_original_func'):
                original_func = minimax._alpha_beta._original_func
            else:
                original_func = minimax._alpha_beta
                
            # Apply new wrapper
            minimax._alpha_beta = self.tracker.track(original_func)
            # Store reference to original function
            minimax._alpha_beta._original_func = original_func
            
            if max_depth is None:
                max_depth = self.max_depth
            
            if self.start_with_maximizing:
                maximizing_player_id = running_player_id
            else:
                maximizing_player_id = abs(running_player_id - 1) # 0 if player 1, 1 if player 0: the other player

            game_score, action = minimax.alpha_beta_search(game, state, self.score_function, maximum_depth=max_depth, maximizing_player_id=maximizing_player_id)

            self.last_choice = self.nodes[self.tracker.root.id + '_' + str(action)]
            return game_score, action
        except Exception as e:
            raise ValueError("You may have forgotten to set the translate game state for the algorithm.") from e

    def visualize_decision_tree(self, root_node):
        dot = graphviz.Digraph(comment='Visualize Decision Tree')
        dot.attr('node', shape='rectangle', style='filled', fontname='Arial', fontsize='10')

        def add_node_to_graph(node, parent_id=None, count_nodes = 0):
            if not node.has_score:
                return count_nodes
            
            count_nodes += 1
            
            node_id = str(node.id)
            label = node_id
            
            # Color coding
            if node.is_leaf:
                fillcolor = 'lightblue'
            elif node.maximizing_player_turn:
                fillcolor = 'green' if node.fully_searched else 'lightgreen'
            else:
                fillcolor = 'deeppink' if node.fully_searched else 'pink'
            
            # Node label
            label += f"\nScore: {node.score}"
            
            dot.node(node_id, label, fillcolor=fillcolor)
            
            if parent_id:
                dot.edge(parent_id, node_id)
            
            for child in node.children:
                count_nodes = add_node_to_graph(child, node_id, count_nodes)
            
            # Add red X for pruned nodes
            if not node.fully_searched:
                prune_id = f"{node_id}_prune"
                pruned_label = "max depth reached" if node.max_search_depth_reached else "pruned"
                dot.node(prune_id, pruned_label, color='white', fontcolor='red', shape='plaintext')
                dot.edge(node_id, prune_id, color='red')
            
            return count_nodes

        count_nodes = add_node_to_graph(root_node)
        if count_nodes > 1000:
            raise Exception(f"Too many nodes ({count_nodes}) to visualize.")
        elif count_nodes > 50: # More than 50 nodes but less than 1000
            dot.attr(layout="twopi")
            dot.attr(overlap='scale') # Don't overlap nodes
        else: # Less than 50 nodes
            dot.attr(rankdir='TB')  # Left to Right or Top to Bottom layout
            dot.attr(dpi='300')  # Set high resolution
        
        dot.attr(root=str(root_node.id))

        # Render the graph
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_filename = tmp_file.name

        dot.render(tmp_filename, format='png', cleanup=True, )
        
        return tmp_filename + '.png'

    def visualize_legend_move_tree(self):
        dot = graphviz.Digraph(comment='Legend')
        dot.attr(dpi='200')  # Set high resolution
        dot.attr('node', shape='rectangle', style='filled', fontname='Arial', fontsize='10')

        dot.attr(label='Legend')
        dot.attr(labelloc='t')  # 't' for top, 'b' for bottom (default)
        
        dot.attr(fontsize='12', fontweight='bold')
        dot.node('legend_maximizer', 'Maximizer turn', fillcolor='green', style='filled')
        dot.node('legend_maximizer_pruned', 'Maximizer turn\n(pruned)', fillcolor='lightgreen', style='filled')
        dot.node('legend_minimizer', 'Minimizer turn', fillcolor='deeppink', style='filled')
        dot.node('legend_minimizer_pruned', 'Minimizer turn\n(pruned)', fillcolor='pink', style='filled')
        dot.node('legend_leaf', 'Leaf Node', fillcolor='lightblue', style='filled')

        # Render the graph
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_filename = tmp_file.name

        dot.render(tmp_filename, format='png', cleanup=True)
        
        return tmp_filename + '.png'