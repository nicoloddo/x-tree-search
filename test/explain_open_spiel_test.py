import pyspiel
from open_spiel.python.algorithms import minimax
from open_spiel.python.observation import make_observation

class GameTreeNode:
    def __init__(self, state, action=None):
        self.state = state
        self.action = action
        self.children = []
        self.value = None

def build_game_tree(game, max_depth=1000000):
    root = GameTreeNode(game.new_initial_state())
    
    def expand_node(node, depth):
        if depth == 0 or node.state.is_terminal():
            return
        
        _, action = minimax.alpha_beta_search(game, state=node.state, maximum_depth=1)
        
        if node.state.is_chance_node():
            for outcome, _ in node.state.chance_outcomes():
                child_state = node.state.child(outcome)
                child_node = GameTreeNode(child_state, outcome)
                node.children.append(child_node)
                expand_node(child_node, depth - 1)
        elif action is not None:
            child_state = node.state.child(action)
            child_node = GameTreeNode(child_state, action)
            node.children.append(child_node)
            expand_node(child_node, depth - 1)
    
    expand_node(root, max_depth)
    return root

def print_game_tree(node, depth=0):
    indent = "  " * depth
    action_str = f" (action: {node.action})" if node.action is not None else ""
    print(f"{indent}State: {node.state}{action_str}")
    
    if node.state.is_terminal():
        print(f"{indent}Terminal state. Returns: {node.state.returns()}")
    else:
        print(f"{indent}Current player: {node.state.current_player()}")
        print(f"{indent}Legal actions: {node.state.legal_actions()}")
    
    observation = make_observation(game)
    for player in range(game.num_players()):
        print(f"{indent}Observation string (player {player}): {observation.string_from(node.state, player)}")
    
    print(f"{indent}History: {node.state.history()}")
    print()
    
    for child in node.children:
        print_game_tree(child, depth + 1)

# Example usage
if __name__ == "__main__":
    game = pyspiel.load_game("tic_tac_toe")
    root = build_game_tree(game, max_depth=5)  # Limit depth for demonstration
    print_game_tree(root)