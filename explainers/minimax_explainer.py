from src.explainer.explainer import ArgumentativeExplainer
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import (
    BooleanAdjective,
    PointerAdjective,
    QuantitativePointerAdjective,
    NodesGroupPointerAdjective,
    ComparisonAdjective,
    MaxRankAdjective,
    MinRankAdjective,
)
from src.explainer.explanation import (
    Possession,
    Assumption,
    If,
    ConditionalExplanation,
    CompositeExplanation,
)

from src.explainer.explanation_tactics import (
    CompactComparisonsWithSameExplanation,
)

game_end_conditional_explanation = ConditionalExplanation(
    condition=If("possession", "a win"),
    explanation_if_true=Possession("a win"),
    explanation_if_false=ConditionalExplanation(
        condition=If("possession", "a loss"),
        explanation_if_true=Possession("a loss"),
        explanation_if_false=Possession("a draw"),
    ),
)


class MiniMaxExplainer:
    """
    A factory class that returns an instance of ArgumentativeExplainer
    configured for MiniMax explanations.
    """

    def __new__(cls, *args, **kwargs):
        """
        Create and return an instance of ArgumentativeExplainer
        configured for MiniMax explanations.

        Returns:
            An instance of ArgumentativeExplainer
        """
        explainer = ArgumentativeExplainer()

        # Add lowlevel framework
        lowlevel_adjectives = cls._get_lowlevel_adjectives()
        lowlevel_settings = {
            "explanation_depth": 3,
            "print_implicit_assumptions": True,
            "assumptions_verbosity": "verbose",
            "print_mode": "logic",
        }

        lowlevel_framework = ArgumentationFramework(
            refer_to_nodes_as="node",
            adjectives=lowlevel_adjectives,
            main_explanation_adjective="best",
            settings=lowlevel_settings,
        )

        # Add highlevel framework
        highlevel_adjectives = cls._get_highlevel_adjectives()

        highlevel_settings = {
            "explanation_depth": 4,
            "print_implicit_assumptions": False,
            "assumptions_verbosity": "if_asked",
            "print_mode": "verbal",
        }

        highlevel_framework = ArgumentationFramework(
            refer_to_nodes_as="move",
            adjectives=highlevel_adjectives,
            main_explanation_adjective="the best",
            settings=highlevel_settings,
        )

        explainer.add_framework("highlevel", highlevel_framework)
        explainer.add_framework("lowlevel", lowlevel_framework)

        return explainer

    @staticmethod
    def _get_lowlevel_adjectives():
        """
        Returns a list of adjective definitions for the lowlevel argumentation framework.
        """
        return [
            BooleanAdjective("leaf", definition="node.is_leaf"),
            QuantitativePointerAdjective(
                "score",
                definition="node.readable_score",
                explanation=ConditionalExplanation(
                    condition=If("possession", "leaf"),
                    explanation_if_true=Assumption(
                        "Leaf nodes have scores from the evaluation function"
                    ),
                    explanation_if_false=CompositeExplanation(
                        Assumption("Internal nodes have scores from children"),
                        Possession("backpropagating child", "score"),
                    ),
                ),
            ),
            BooleanAdjective(
                "opponent player turn", definition="not node.maximizing_player_turn"
            ),
            PointerAdjective(
                "backpropagating child",
                definition="node.score_child",
                explanation=ConditionalExplanation(
                    condition=If("possession", "opponent player turn"),
                    explanation_if_true=CompositeExplanation(
                        Assumption("We assume the opponent will do their best move."),
                        Possession("backpropagating child", "worst"),
                    ),
                    explanation_if_false=CompositeExplanation(
                        Assumption("On our turn we take the maximum rated move."),
                        Possession("backpropagating child", "best"),
                    ),
                ),
            ),
            ComparisonAdjective("better than", "score", ">="),
            NodesGroupPointerAdjective(
                "siblings", definition="node.parent.children", excluding="node"
            ),
            MaxRankAdjective("best", ["better than"], "siblings"),
            MinRankAdjective("worst", ["better than"], "siblings"),
        ]

    @staticmethod
    def _get_highlevel_adjectives():
        """
        Returns a list of adjective definitions for the highlevel argumentation framework.
        """
        return [
            BooleanAdjective(
                "the most forward in the future I looked",
                definition="node.max_search_depth_reached",
            ),
            BooleanAdjective(
                "final move",
                definition="node.final_node",
                explanation=ConditionalExplanation(
                    condition=If(
                        "possession", "the most forward in the future I looked"
                    ),
                    explanation_if_true=Possession(
                        "the most forward in the future I looked"
                    ),
                    explanation_if_false=game_end_conditional_explanation,
                ),
            ),
            BooleanAdjective(
                "a win",
                definition="node.final_node and node.score > 0",
                explanation=Assumption("These are the rules!"),
            ),
            BooleanAdjective(
                "a loss",
                definition="node.final_node and node.score < 0",
                explanation=Assumption("These are the rules!"),
            ),
            BooleanAdjective(
                "a draw",
                definition="node.final_node and node.score == 0",
                explanation=Assumption("These are the rules!"),
            ),
            QuantitativePointerAdjective(
                "score",
                definition="node.readable_score",
                skip_statement=True,
                explanation=ConditionalExplanation(
                    condition=If("possession", "final move"),
                    # It's a final move: we say if it is a win, loss or draw
                    explanation_if_true=game_end_conditional_explanation,
                    # Not a final move: explain using backpropagating child
                    explanation_if_false=ConditionalExplanation(
                        condition=If(
                            "possession", "the most forward in the future I looked"
                        ),
                        explanation_if_true=CompositeExplanation(
                            Possession("the most forward in the future I looked"),
                            Assumption(
                                "when I can't look further in the future, my evaluation of a move is qualitative, only based on the board position after it",
                                necessary=True,
                            ),
                        ),
                        explanation_if_false=CompositeExplanation(
                            Assumption(
                                "We assume us and the opponent are playing optimally."
                            ),
                            Possession("as next move"),
                        ),
                    ),
                ),
            ),
            BooleanAdjective(
                "opponent player turn", definition="not node.maximizing_player_turn"
            ),
            PointerAdjective(
                "as next move",
                definition="node.score_child",
                explanation=CompositeExplanation(
                    Assumption("We assume us and the opponent are playing optimally."),
                    Possession("as next move", "the best"),
                ),
            ),
            ComparisonAdjective("better for me than", "score", ">"),
            ComparisonAdjective("worse for me than", "score", "<"),
            ComparisonAdjective("equal to", "score", "=="),
            NodesGroupPointerAdjective(
                "possible alternatives",
                definition="node.parent.children",
                excluding="node",
            ),
            MaxRankAdjective(
                "the best",
                ["better for me than", "at least equal to"],
                "possible alternatives",
                explain_with_adj_if=(
                    If("possession", "opponent player turn"),
                    "the best for me",
                    "the best for opponent",
                ),
            ),
            MaxRankAdjective(
                "the best for me",
                ["better for me than", "equal to"],
                "possible alternatives",
                explain_with_adj_if=(
                    If("possession", "opponent player turn", value=False),
                    "the best for opponent",
                ),
                tactics=[
                    CompactComparisonsWithSameExplanation(
                        from_adjectives=["as next move"],
                        same_if_equal_keys=[("evaluation", ["depth", "last_move_id"])],
                    )
                ],
            ),
            MaxRankAdjective(
                "the best for opponent",
                ["worse for me than", "equal to"],
                "possible alternatives",
                explain_with_adj_if=(
                    If("possession", "opponent player turn"),
                    "the best for me",
                ),
                tactics=[
                    CompactComparisonsWithSameExplanation(
                        from_adjectives=["as next move"],
                        same_if_equal_keys=[("evaluation", ["depth", "last_move_id"])],
                    )
                ],
            ),
        ]
