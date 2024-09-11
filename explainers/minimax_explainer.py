from src.explainer.explainer import ArgumentativeExplainer
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import BooleanAdjective, PointerAdjective, QuantitativePointerAdjective, NodesGroupPointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective
from src.explainer.explanation import Possession, Assumption, If, ConditionalExplanation, CompositeExplanation

from src.explainer.explanation_tactics import OnlyRelevantComparisons, SkipQuantitativeExplanations, SubstituteQuantitativeExplanations

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

        explainer.add_framework("lowlevel", 
            ArgumentationFramework(refer_to_nodes_as = 'node',
                
                adjectives = [
                
                    BooleanAdjective("leaf",
                        definition = "node.is_leaf"),


                    QuantitativePointerAdjective("score",
                        definition = "node.score",

                        explanation = ConditionalExplanation(
                            condition = If("leaf"),
                            explanation_if_true = Assumption("Leaf nodes have scores from the evaluation function"),
                            explanation_if_false = CompositeExplanation(
                                Assumption("Internal nodes have scores from children"),
                                Possession("backpropagating child", "score"))
                        )),


                    BooleanAdjective("opponent player turn",
                        definition = "not node.maximizing_player_turn"),


                    PointerAdjective("backpropagating child",
                        definition = "node.score_child",

                        explanation = ConditionalExplanation(
                            condition = If("opponent player turn"),
                            explanation_if_true = CompositeExplanation(
                                Assumption("We assume the opponent will do their best move."),
                                Possession("backpropagating child", "worst")),
                            explanation_if_false = CompositeExplanation(
                                Assumption("On our turn we take the maximum rated move."),
                                Possession("backpropagating child", "best"))
                        )),

                    ComparisonAdjective("better", "score", ">="),
                
                    NodesGroupPointerAdjective("siblings",
                        definition = "node.parent.children",
                        excluding = "node"),

                    MaxRankAdjective("best", "better", "siblings"),

                    MinRankAdjective("worst", "better", "siblings"),
                ],

                settings = {
                    'explanation_depth': 3 ,
                    'print_implicit_assumptions': True,
                    'assumptions_verbosity': 'verbose',
                    'print_mode': 'logic'
                }
            )
        )

        explainer.add_framework("highlevel", 
            ArgumentationFramework(refer_to_nodes_as = 'move',

                adjectives = [
                
                    BooleanAdjective("final move",
                        definition = "node.is_leaf"),


                    QuantitativePointerAdjective("score",
                        definition = "node.score",

                        explanation = ConditionalExplanation(
                            condition = If("final move"),
                            explanation_if_true = Assumption("final moves are evaluated only looking at the final position", necessary=True),
                            explanation_if_false = CompositeExplanation(
                                Possession("next possible move", "score"))
                        )),
                    

                    BooleanAdjective("opponent player turn",
                        definition = "not node.maximizing_player_turn"),


                    PointerAdjective("next possible move",
                        definition = "node.score_child",

                        explanation = ConditionalExplanation(
                            condition = If("opponent player turn"),
                            explanation_if_true = CompositeExplanation(
                                Assumption("we assume the opponent will do their best move"),
                                Possession("next possible move", "the best the opponent can do")),
                            explanation_if_false = CompositeExplanation(
                                Assumption("on our turn we take the maximum rated move"),
                                Possession("next possible move", "the best"))
                        )),

                    ComparisonAdjective("better", "score", ">="),
                
                    NodesGroupPointerAdjective("possible alternative moves",
                        definition = "node.parent.children",
                        excluding = "node"),

                    MaxRankAdjective("the best", "better", "possible alternative moves",
                                    tactics = [OnlyRelevantComparisons(mode = "top_3")]),

                    MinRankAdjective("the best the opponent can do", "better", "possible alternative moves"),
                ],
                
                tactics=[
                    SubstituteQuantitativeExplanations("it leads to a better position")
                ],

                settings = {
                    'explanation_depth': 4 ,
                    'print_implicit_assumptions': False,
                    'assumptions_verbosity': 'if_asked',
                    'print_mode': 'verbal'
                }
            )
        )

        return explainer