from src.explainer.explainer import ArgumentativeExplainer
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import BooleanAdjective, PointerAdjective, QuantitativePointerAdjective, NodesGroupPointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective
from src.explainer.explanation import Possession, Assumption, Comparison, If, ConditionalExplanation, CompositeExplanation

from src.explainer.explanation_tactics import OnlyRelevantComparisons, SkipQuantitativeExplanations, SubstituteQuantitativeExplanations, SkipConditionStatement

class AlphaBetaExplainer:
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
                                Possession("next move", "score")),
                        ),

                        if_none_refer_to_adjective = "irrelevant"
                        ),
                    

                    BooleanAdjective("opponent player turn",
                        definition = "not node.maximizing_player_turn"),


                    PointerAdjective("next move",
                        definition = "node.score_child",

                        explanation = ConditionalExplanation(
                            condition = If("opponent player turn"),
                            explanation_if_true = CompositeExplanation(
                                Assumption("we assume the opponent will do their best move"),
                                Possession("next move", "the best the opponent can do")),
                            explanation_if_false = CompositeExplanation(
                                Assumption("on our turn we take the maximum rated move"),
                                Possession("next move", "the best"))
                        )),

                    BooleanAdjective("irrelevant",
                        definition = "not node.fully_searched",
                        
                        explanation = ConditionalExplanation(
                                condition = If("opponent player turn"),
                                explanation_if_true = CompositeExplanation(
                                    Possession("next move"),
                                    Comparison("next move", "worse or equal", "what we could choose previously"),
                                ),
                                explanation_if_false = CompositeExplanation(
                                    Possession("next move"),
                                    Comparison("next move", "better or equal", "what the opponent could choose previously")
                                )
                            )
                    ),

                    PointerAdjective("what the opponent could choose previously",
                        definition = "node.beta",
                        explanation = Assumption("We assume the opponent will do their best move.")),

                    PointerAdjective("what we could choose previously",
                        definition = "node.alpha",
                        explanation = Assumption("On our turn we take the maximum rated move.")),

                    ComparisonAdjective("better or equal", "score", ">=", if_none_return=True),

                    ComparisonAdjective("worse or equal", "score", "<=", if_none_return=True),
                
                    NodesGroupPointerAdjective("possible alternative moves",
                        definition = "node.parent.children",
                        excluding = "node"),

                    MaxRankAdjective("the best", "better or equal", "possible alternative moves"),

                    MaxRankAdjective("the best the opponent can do", "worse or equal", "possible alternative moves"),
                ],
                
                tactics=[
                    #SubstituteQuantitativeExplanations("it leads to a better or equal position"),
                ],

                settings = {
                    'explanation_depth': 4 ,
                    'print_implicit_assumptions': False,
                    'assumptions_verbosity': 'verbose',
                    'print_mode': 'verbal'
                }
            )
        )

        return explainer
    


"""Alternative:

                    BooleanAdjective("not worth exploring",
                        definition = "not node.has_score",
                        
                        explanation = ConditionalExplanation(
                            condition = If("opponent player turn"),
                            explanation_if_true = CompositeExplanation(
                                Assumption("The opponent would choose this bad sibling, or even worse."),
                                Comparison("bad sibling", "worse", "what we could choose at the previous move")
                            ),
                            explanation_if_false = CompositeExplanation(
                                Assumption("On our turn we would choose this good sibling, or even better."),
                                Comparison("good sibling", "better", "what the opponent could choose at the previous move")
                        ))),
                    
                    PointerAdjective("good sibling",
                        definition = "node.parent.alpha",
                        explanation = Possession("siblings")),

                    PointerAdjective("bad sibling",
                        definition = "node.parent.beta",
                        explanation = Possession("siblings")),
"""