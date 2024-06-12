from src.tree import Tree
from src.game_model import GameModel

class GameTree(Tree):
    def __init__(self, game, scoring_function, action_space_id):
        """
        Initializes the GameTree object which builds upon the Tree class.

        The GameTree is designed to represent the possible states and actions in a given game. To create a GameTree, you need a game model, a scoring function, and an action space identifier.

        The game parameter must be an instance of GameModel, which includes defining agents, action spaces, and rules. Action spaces are the areas or elements where actions can be performed, such as a board in tic-tac-toe. Each action space can have modifiable elements or slots. The agents variable refers to an action space that allows agents to perform actions on other agents and modify their features. Rules constrain these action spaces by limiting the possible actions.

        The scoring_function should be a callable that takes one input called state, which is used to evaluate the game states. The function must be defined to appropriately score the states of the game.

        The action_space_id is an identifier for the action space on which to build the game tree. This specifies the area or context within the game where the actions are evaluated and performed.

        Args:
            game (GameModel): An instance of the GameModel class which includes agents, action spaces, and rules.
            scoring_function (function): A callable function that takes one input (state) and returns a score evaluating that state.
            action_space_id (str): Identifier for the action space used to build the game tree.

        Attributes:
            game (GameModel): The game model instance.
            score (function): The scoring function to evaluate game states.
            action_space_id (str): Identifier for the relevant action space in the game model.

        Raises:
            ValueError: If game is not an instance of GameModel.
            ValueError: If scoring_function is not callable.

        """
        super().__init__()
        if not isinstance(game, GameModel):
            raise ValueError("The game of the GameTree must be a valid GameModel object.")
        if not callable(scoring_function):
            raise ValueError("The scoring_function must be a callable function.")

        self.game = game
        self.score = scoring_function
        self.action_space_id = action_space_id

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
            score (number) (derived)
            action (dict) (derived)
        """
        def __init__(self, parent, value):
            mandatory_features = ["state", "score", "action"]
            if not all(features in value for features in mandatory_features):
                raise ValueError(f"All mandatory features should be in the GameTreeNode value: {mandatory_features}")

            super.__init__(self, parent, value)

        @property
        def state(self):
            return self.value["state"]
        @property
        def score(self):
            return self.value["score"]
        @property
        def action(self):
            return self.value["action"]

        @state.setter
        def state(self, value):
            self.value["state"] = value
        @score.setter
        def score(self, value):
            self.value["score"] = value
        @action.setter
        def action(self, value):
            self.value["action"] = value

    def expand_node(node_id):
        node = self.nodes[node_id]

        state = node.state
        staste_rules_id = self.action_space_id

        available_actions_and_states = self.game.get_available_actions_and_states(state, staste_rules_id)

        children_values = []
        for actions_and_states in available_actions_and_states:
            action = actions_and_states["action"]
            state = actions_and_states["state"]
            score = self.score(state)

            value = {"state": state, "score": score, "action": action}
            children_values.append(value)

        set_children(self, node_id, children_values)