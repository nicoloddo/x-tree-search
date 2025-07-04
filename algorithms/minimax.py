from typing import Dict
import copy

import graphviz
import tempfile


class MiniMaxNode:
    """
    A wrapper for nodes in the game tree for use with the MiniMax algorithm.

    Attributes:
        node (object): The original node from the game tree.
        score (float): The score assigned to the node by the MiniMax algorithm.
        nodes_holder (list): Pointer to the structure that holds all the nodes in the tree.
    """

    score_readability_multiplier = 1000

    @classmethod
    def game_state_translator(cls, state):
        return state

    def __init__(self, node, parent=None, nodes_holder=None):
        self.node = node
        self.parent = parent
        if self.parent is not None:
            self.parent_state = self.game_state_translator(
                copy.deepcopy(parent.node.state)
            )
        else:
            self.parent_state = None
        self.children = []

        if nodes_holder is None:
            nodes_holder = {}
        self.nodes_holder = nodes_holder
        self.nodes_holder[self.id] = self

        self.depth = None
        self.score = None
        self.fully_searched = None
        self.alpha = None
        self.beta = None
        self.maximizing_player_turn = None
        self.score_child = None
        self.max_search_depth_reached = False

    @property
    def id(self):
        return self.node.id

    @property
    def game_state(self):
        return self.game_state_translator(self.node.state)

    @property
    def game_tree_node_string(self):
        return str(self.node)

    @property
    def action_description(self):
        return str(self.node)

    def expand(self, with_constraints=None):
        # Expands the node by one depth.
        self.node.expand(with_constraints)
        self.children = self.populate_children()

    def populate_children(self):
        return [
            MiniMaxNode(child, self, self.nodes_holder) for child in self.node.children
        ]

    def get_deep_score_child(self):
        if self.score_child is not None:
            return self.score_child.get_deep_score_child()
        else:
            return self

    @property
    def deep_score_child(self):
        return self.get_deep_score_child()

    @property
    def is_leaf(self):
        return self.node.is_leaf

    @property
    def final_node(self):
        return self.is_leaf and not self.max_search_depth_reached

    @property
    def id_length(self):
        return len(self.id)

    @property
    def last_move_id(self):
        return self.id[-1]

    @property
    def action(self):
        return self.node.action

    @property
    def readable_score(self):
        return self.score * MiniMaxNode.score_readability_multiplier

    @property
    def has_score(self):
        return self.score is not None

    @property
    def explicit_description(self):
        return "\n" + f"{str(self.game_state)} {str(self.game_tree_node_string)}"

    def __str__(self) -> str:
        return f"{self.explicit_description}, id={self.id}" + ""


class MiniMax:
    """
    Implements the MiniMax algorithm with optional Alpha-Beta pruning to determine the optimal child of a node.

    Attributes:
        scoring_function (callable): A function that takes a node state and returns a numerical score.
        use_alpha_beta (bool): Whether to use alpha-beta pruning.
    """

    tree_node_class = MiniMaxNode

    @classmethod
    def set_game_state_translator(cls, game_state_translator):
        cls.tree_node_class.game_state_translator = game_state_translator

    def __init__(
        self,
        scoring_function,
        *,
        max_depth=3,
        start_with_maximizing=True,
        use_alpha_beta=True,
    ):
        # Mandatory attributes:
        self.nodes = {}  # Holds the nodes with as key their node.node.id
        self.last_choice = None

        # Other attributes:
        self.score = scoring_function
        self.search_root = None
        self.search_root_final = None
        self.start_with_maximizing = start_with_maximizing

        # Instance variables instead of class variables
        self.max_depth = max_depth
        self.use_alpha_beta = use_alpha_beta

    def set_max_depth(self, max_depth):
        """Set the maximum search depth for this MiniMax instance."""
        self.max_depth = max_depth

    def set_use_alpha_beta(self, use_alpha_beta):
        """Set whether to use alpha-beta pruning for this MiniMax instance."""
        self.use_alpha_beta = use_alpha_beta

    def run(
        self,
        state_node,
        *,
        max_depth=None,
        expansion_constraints_self: Dict = None,
        expansion_constraints_other: Dict = None,
    ):
        try:
            if self.use_alpha_beta:
                algorithm = self.alphabeta
            else:
                algorithm = self.minimax

            if max_depth is None:
                max_depth = self.max_depth

            self.search_root = MiniMaxNode(state_node)
            self.nodes = self.search_root.nodes_holder

            best_child, best_value = algorithm(
                self.search_root,
                self.start_with_maximizing,
                max_depth=max_depth,
                constraints_maximizer=expansion_constraints_self,
                constraints_minimizer=expansion_constraints_other,
            )

            if best_child is not None:
                self.search_root_final = best_child.parent
                self.last_choice = best_child
            return best_child, best_value
        except Exception as e:
            raise ValueError(
                "You may have forgotten to set the translate game state for the algorithm."
            ) from e

    def minimax(
        self,
        node,
        is_maximizing,
        current_depth=0,
        *,
        max_depth,
        constraints_maximizer=None,
        constraints_minimizer=None,
    ):
        node.fully_searched = True  # The node will be fully searched in minimax always.
        node.maximizing_player_turn = is_maximizing
        node.depth = current_depth
        if current_depth >= max_depth:
            node.score = self.score(node)
            node.max_search_depth_reached = True
            return None, None
        else:
            with_constraints = (
                constraints_maximizer if is_maximizing else constraints_minimizer
            )
            node.expand(with_constraints)

        # If the node is a leaf, or if we reached the max search depth, return its score
        if node.is_leaf:
            node.score = self.score(node)
            return None, None

        # Initialize best value
        if is_maximizing:
            best_value = float("-inf")
        else:
            best_value = float("inf")

        best_child = None

        for child in node.children:
            # If child does not have a score, recursively call minimax on the child
            if not child.has_score:
                _, _ = self.minimax(
                    child,
                    not is_maximizing,
                    current_depth + 1,
                    max_depth=max_depth,
                    constraints_maximizer=constraints_maximizer,
                    constraints_minimizer=constraints_minimizer,
                )

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

    def alphabeta(
        self,
        node,
        is_maximizing,
        current_depth=0,
        alpha=None,
        beta=None,
        *,
        max_depth,
        constraints_maximizer=None,
        constraints_minimizer=None,
    ):
        node.maximizing_player_turn = is_maximizing
        node.depth = current_depth

        if alpha is None:
            node.alpha = None
            alpha = float("-inf")
        else:
            node.alpha = alpha
            alpha = alpha.score

        if beta is None:
            node.beta = None
            beta = float("inf")
        else:
            node.beta = beta
            beta = beta.score

        with_constraints = (
            constraints_maximizer if is_maximizing else constraints_minimizer
        )
        node.expand(with_constraints)

        # If the node is a leaf, or if we reached the max search depth, return its score
        if node.is_leaf:
            node.score = self.score(node)
            node.fully_searched = True
            return None, None
        elif current_depth >= max_depth:
            node.score = self.score(node)
            node.max_search_depth_reached = True
            return None, None

        # Initialize best value
        if is_maximizing:
            best_value = float("-inf")
        else:
            best_value = float("inf")

        best_child = None
        for i, child in enumerate(node.children):
            # If child does not have a score, recursively call minimax on the child
            if not child.has_score:
                _, _ = self.alphabeta(
                    child,
                    not is_maximizing,
                    current_depth + 1,
                    node.alpha,
                    node.beta,
                    max_depth=max_depth,
                    constraints_maximizer=constraints_maximizer,
                    constraints_minimizer=constraints_minimizer,
                )

            # Update the best value and best move depending on the player
            if is_maximizing:  # Maximizing player turn
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

            else:  # Minimizer player turn
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

        if i + 1 == len(node.children):
            node.fully_searched = True

        # Assign the best value to the current node
        node.score_child = best_child
        node.score = best_value

        return best_child, best_value

    def get_node(self, node_id: str):
        return self.nodes[node_id]

    def print_tree(self, node=None, level=0, is_score_child=False):
        if node is None:
            node = self.search_root_final

        indent = "  " * 2 * level
        score_indicator = "*" if is_score_child else ""
        maximizer_string = "maximizer" if node.maximizing_player_turn else "minimizer"

        leaf_string = "leaf" if node.is_leaf else " "

        fully_searched_string = "fully searched" if node.fully_searched else "pruned"

        if node.alpha is None:
            alpha_string = "None"
        else:
            alpha_string = node.alpha.id

        if node.beta is None:
            beta_string = "None"
        else:
            beta_string = node.beta.id

        print(
            f"{indent}{score_indicator}Node {node.id}: Score = {node.score} Alpha = {alpha_string} Beta = {beta_string} ({maximizer_string}, {fully_searched_string}) ({leaf_string})"
        )

        for child in node.children:
            self.print_tree(child, level + 1, child == node.score_child)

    def visualize_decision_tree(self, root_node):
        dot = graphviz.Digraph(comment="Visualize Decision Tree")
        dot.attr(
            "node", shape="rectangle", style="filled", fontname="Arial", fontsize="10"
        )

        def add_node_to_graph(node, parent_id=None, count_nodes=0):
            if not node.has_score:
                return count_nodes

            count_nodes += 1

            node_id = str(node.id)
            label = node_id

            # Color coding
            if node.is_leaf:
                fillcolor = "lightblue"
            elif node.maximizing_player_turn:
                fillcolor = "green" if node.fully_searched else "lightgreen"
            else:
                fillcolor = "deeppink" if node.fully_searched else "pink"

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
                pruned_label = (
                    "max depth reached" if node.max_search_depth_reached else "pruned"
                )
                dot.node(
                    prune_id,
                    pruned_label,
                    color="white",
                    fontcolor="red",
                    shape="plaintext",
                )
                dot.edge(node_id, prune_id, color="red")

            return count_nodes

        count_nodes = add_node_to_graph(root_node)
        if count_nodes > 1000:
            raise Exception(f"Too many nodes ({count_nodes}) to visualize.")
        elif count_nodes > 50:  # More than 50 nodes but less than 1000
            dot.attr(layout="twopi")
            dot.attr(overlap="scale")  # Don't overlap nodes
        else:  # Less than 50 nodes
            dot.attr(rankdir="TB")  # Left to Right or Top to Bottom layout
            dot.attr(dpi="300")  # Set high resolution

        dot.attr(root=str(root_node.id))

        # Render the graph
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_filename = tmp_file.name

        dot.render(
            tmp_filename,
            format="png",
            cleanup=True,
        )

        return tmp_filename + ".png"

    def visualize_legend_move_tree(self):
        dot = graphviz.Digraph(comment="Legend")
        dot.attr(dpi="200")  # Set high resolution
        dot.attr(
            "node", shape="rectangle", style="filled", fontname="Arial", fontsize="10"
        )

        dot.attr(label="Legend")
        dot.attr(labelloc="t")  # 't' for top, 'b' for bottom (default)

        dot.attr(fontsize="12", fontweight="bold")
        dot.node(
            "legend_maximizer", "Maximizer turn", fillcolor="green", style="filled"
        )
        dot.node(
            "legend_maximizer_pruned",
            "Maximizer turn\n(pruned)",
            fillcolor="lightgreen",
            style="filled",
        )
        dot.node(
            "legend_minimizer", "Minimizer turn", fillcolor="deeppink", style="filled"
        )
        dot.node(
            "legend_minimizer_pruned",
            "Minimizer turn\n(pruned)",
            fillcolor="pink",
            style="filled",
        )
        dot.node("legend_leaf", "Leaf Node", fillcolor="lightblue", style="filled")

        # Render the graph
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_filename = tmp_file.name

        dot.render(tmp_filename, format="png", cleanup=True)

        return tmp_filename + ".png"
