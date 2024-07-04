from src.structures.tree import Tree
from src.game.game_model import GameModel

class GameTree(Tree):
    def __init__(self, game, scoring_function, action_space_id):
        """
        Initializes the GameTree object which builds upon the Tree class.

        The GameTree is designed to represent the possible states and actions in a given game. To create a GameTree, you need a game model, a scoring function, and an action space identifier.

        The game parameter must be an instance of GameModel, which includes defining agents, action spaces, and rules. Action spaces are the areas or elements where actions can be performed, such as a board in tic-tac-toe. Each action space can have modifiable elements or slots. The agents variable refers to an action space that allows agents to perform actions on other agents and modify their features. Rules constrain these action spaces by limiting the possible actions.

        The state is a numpy.ndarray matrix with elements belonging to the available_labels in the game.action_spaces[action_spaces_id].

        The action_space_id is an identifier for the action space on which to build the game tree. This specifies the area or context within the game where the actions are evaluated and performed.

        Args:
            game (GameModel): An instance of the GameModel class which includes agents, action spaces, and rules.
            action_space_id (str): Identifier for the action space used to build the game tree.

        Attributes:
            game (GameModel): The game model instance.
            action_space_id (str): Identifier for the relevant action space in the game model.

        Raises:
            ValueError: If game is not an instance of GameModel.
            ValueError: If scoring_function is not callable.

        """
        super().__init__()
        if not isinstance(game, GameModel):
            raise ValueError("The game of the GameTree must be a valid GameModel object.")

        self.game = game
        self.action_space_id = action_space_id

        self.root = self.__add_node(game=self.game)
        self.root.state = game.action_spaces[action_space_id]

    class GameTreeNode(Tree.TreeNode):
        """
        Represents a single node in a game tree. Check the Tree.TreeNode documentation for more info. 
        The only modification from the standard TreeNode is the value of node.value which becomes specifically a dict with mandatory keys.
        The values of the value dict are mapped to properties. 

        Attributes:
            parent (TreeNode): The TreeNode parent of this node. If it is None, this is the root node, identified with the id:"0".
            is_leaf (bool): Indicates whether this node is a leaf of the tree.
            value (dict): Dictionary containing mandatory keys to use.
            children (list) (derived): A list of Node instances that are the children of this node (derived property from the original MarkovNode.connections attribute)
            children_and_probs (list) (derived): List of tuples containing children of this node and the respective transition probability
            state (GameModel.ActionSpace) (derived)
            action (dict) (derived)
            game
        """
        def __init__(self, parent, value, game=None):
            mandatory_features = ["state", "action", "game"]

            if not parent and not value and game: # Root node
                value = {}
                for feature in mandatory_features:
                    value[feature] = None
                value["game"] = game
            elif not parent and not value and not game:
                raise ValueError("You should specify the game when initializing a root node.")
            elif not parent:
                raise ValueError("Not root nodes must have a parent specified at initialization.")
            else:
                if not all(features in value for features in mandatory_features):
                    raise ValueError(f"All mandatory features should be in the GameTreeNode value: {mandatory_features}")

            super().__init__(parent, value)

        @property
        def state(self):
            return self.value["state"]
        @property
        def action(self):
            return self.value["action"]
        @property
        def game(self):
            return self.value["game"]

        @state.setter
        def state(self, value):
            self.value["state"] = value
        @action.setter
        def action(self, value):
            self.value["action"] = value
        @game.setter
        def game(self, value):
            self.value["game"] = value

        def expand(self, game_tree):
            state = self.state
            action_space_id = game_tree.action_space_id

            available_actions_and_states = self.game.get_available_actions_and_states(action_space_id)

            children_values = []
            for actions_and_states in available_actions_and_states:
                action = actions_and_states["action"]
                state = actions_and_states["state"]
                game = actions_and_states["game"]

                value = {"state": state, "action": action, "game": game}
                children_values.append(value)

            game_tree.set_children(self.id, children_values)

        def _expand_children(self, game_tree, count_depth, depth):
            if count_depth >= depth:
                return
            
            for child in self.children:
                child.expand(game_tree)
                child._expand_children(game_tree, count_depth + 1, depth)
        
        def expand_to_depth(self, game_tree, depth):
            count_depth = 0

            if depth > 0:
                self.expand(game_tree) # expand root
                count_depth += 1
            
            if depth > 1:
                self._expand_children(game_tree, count_depth, depth)

    def __add_node(self, parent=None, value=None, *, game=None):
        """Overrides the add_node method to ensure GameTreeNode objects are created."""
        new_node = self.GameTreeNode(parent, value, game)
        self.nodes[new_node.id] = new_node
        return new_node

    def set_children(self, node_id, children_values):
        """
        Expands a node with a given amount of children and their values

        Args:
            node (str): The id of the node to expand with new children.
            children_values (list of numbers): Values to assign to the children nodes.
        """
        parent = self.nodes[node_id]
        for value in children_values:
            child = self.__add_node(parent=parent, value=value)
            probability = 1/len(children_values)
            parent._add_child(child, probability)

    def expand_node(self, node_id, depth=1):
        node = self.nodes[node_id]

        node.expand_to_depth(self, depth)