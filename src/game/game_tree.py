from src.structures.tree import Tree
from src.game.game_model import GameModel

class GameTree(Tree):
    def __init__(self, game, action_space_id, node_string_format = "{who} does {what} in {where} on {on} modifying what was {what_before}"):
        """
        Initializes the GameTree object which builds upon the Tree class.

        The GameTree is designed to represent the possible states and actions in a given game. To create a GameTree, you need a game model, a scoring function, and an action space identifier.

        The game parameter must be an instance of GameModel, which includes defining agents, action spaces, and rules. Action spaces are the areas or elements where actions can be performed, such as a board in tic-tac-toe. Each action space can have modifiable elements or slots. The agents variable refers to an action space that allows agents to perform actions on other agents and modify their features. Rules constrain these action spaces by limiting the possible actions.

        The state is a numpy.ndarray matrix with elements belonging to the available_labels in the game.action_spaces[action_spaces_id].

        The action_space_id is an identifier for the action space on which to build the game tree. This specifies the area or context within the game where the actions are evaluated and performed.

        Args:
            game (GameModel): An instance of the GameModel class which includes agents, action spaces, and rules.
            action_space_id (str): Identifier for the action space used to build the game tree.
            node_string_format (str): String format for the node string.

        Attributes:
            game (GameModel): The game model instance.
            action_space_id (str): Identifier for the relevant action space in the game model.
            node_string_format (str): String format for the node string.

        Raises:
            ValueError: If game is not an instance of GameModel.
            ValueError: If scoring_function is not callable.

        """
        super().__init__()
        if not isinstance(game, GameModel):
            raise ValueError("The game of the GameTree must be a valid GameModel object.")

        self.game = game
        self.action_space_id = action_space_id
        self.node_string_format = node_string_format

        self.root = self.__add_node(root_node_bool=True)
        self.root.state = game.action_spaces[action_space_id]
    
    def get_current_state(self):
        """Returns the current node state."""
        return self.root 

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
            belonging_tree
        """
        def __init__(self, parent, value, *, belonging_tree, root_node_bool=False):
            mandatory_features = ["state", "action", "game"]
            self.belonging_tree = belonging_tree

            if root_node_bool: # Root node
                value = {}
                for feature in mandatory_features:
                    value[feature] = None
                value["game"] = belonging_tree.game # Root nodes set the game feature
            else: # Not root node
                if not parent:
                    raise ValueError("Not root nodes must have a parent specified at initialization.")
                if not all(features in value for features in mandatory_features):
                    raise ValueError(f"All mandatory features should be in the GameTreeNode value: {mandatory_features}")
            
            self.expanded = False
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

        def expand(self, with_constraints=None):
            """Expands the node by one depth.
            With the constraints you can limit the expansion to valid moves coming from a specific player for example,
            to avoid getting moves that the current player will not be able to use."""
            game_tree = self.belonging_tree

            if self.expanded:
                return                
            self.expanded = True

            state = self.state
            action_space_id = game_tree.action_space_id

            available_actions_and_states = self.game.get_available_actions_and_states(action_space_id, with_constraints)

            children_values = []
            for actions_and_states in available_actions_and_states:
                action = actions_and_states["action"]
                state = actions_and_states["state"]
                game = actions_and_states["game"]

                value = {"state": state, "action": action, "game": game}
                children_values.append(value)

            game_tree.set_children(self.id, children_values)

        def _expand_children(self, count_depth, depth):            
            if count_depth >= depth:
                return
            
            for child in self.children:
                child.expand()
                child._expand_children(count_depth + 1, depth)
        
        def expand_to_depth(self, depth):
            """The expand_to_depth is acceptable only without constraints, because children might need different constraints
            than a parent. Please use the expand method directly while handling the depth yourself if you need to apply constraints."""

            count_depth = 0

            if depth > 0:
                self.expand() # expand first
                count_depth += 1
            
            if depth > 1:
                self._expand_children(count_depth, depth)

        def __str__(self) -> str:
            if self.action is None:
                return "(No action recorded)"
            node_string_format = self.belonging_tree.node_string_format
            game = self.belonging_tree.game

            composed_string = node_string_format.format(
                who=str(self.action['who']),
                who_game_identifier=game.agents[self.action['who']][0],
                what=str(self.action['what']),
                where=str(self.action['where']),
                on=str(self.action['on']),
                what_before=str(self.action['what_before'])
            )
            return composed_string

    def __add_node(self, parent=None, value=None, *, root_node_bool=False):
        """Overrides the add_node method to ensure GameTreeNode objects are created."""
        new_node = self.GameTreeNode(parent, value, belonging_tree=self, root_node_bool=root_node_bool)
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

    def expand_node_to_depth(self, node_id, *, depth=1):
        node = self.nodes[node_id]

        node.expand_to_depth(depth)