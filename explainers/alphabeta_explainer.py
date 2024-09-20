from src.explainer.explainer import ArgumentativeExplainer
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import BooleanAdjective, PointerAdjective, QuantitativePointerAdjective, NodesGroupPointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective
from src.explainer.explanation import Possession, RecursivePossession, Assumption, Comparison, If, ConditionalExplanation, CompositeExplanation

from src.explainer.explanation_tactics import OnlyRelevantComparisons, SkipQuantitativeExplanations, CompactCollectiveConsequences

class AlphaBetaExplainer:
    """
    A factory class that returns an instance of ArgumentativeExplainer
    configured for AlphaBeta explanations.
    """

    def __new__(cls, *args, **kwargs):
        """
        Create and return an instance of ArgumentativeExplainer
        configured for MiniMax explanations.

        Returns:
            An instance of ArgumentativeExplainer
        """
        explainer = ArgumentativeExplainer()
        
        # Define adjectives
        adjectives = cls._get_adjectives()
        
        # Define tactics
        tactics = [
            # Add your tactics here
            SkipQuantitativeExplanations(),
        ]
        
        # Define settings
        settings = {
            'explanation_depth': 4,
            'print_implicit_assumptions': False,
            'assumptions_verbosity': 'verbose',
            'print_mode': 'verbal',
        }
        
        # Create argumentation framework
        highlevel_framework = ArgumentationFramework(
            refer_to_nodes_as='move',
            adjectives=adjectives,
            tactics=tactics,
            settings=settings,
        )
        
        # Add framework to explainer
        explainer.add_framework("highlevel", highlevel_framework)
        
        return explainer
    
    @staticmethod
    def _get_adjectives():
        """
        Returns a list of adjective definitions for the argumentation framework.
        """

        adjectives = [
            BooleanAdjective("leaf",
                definition = "node.is_leaf"),
            BooleanAdjective("final move",
                definition = "node.final_node"),
            BooleanAdjective("the most forward in the future I looked",
                definition = "node.max_search_depth_reached"),

            BooleanAdjective("a win",
                definition = "node.final_node and node.score > 0",
                explanation = Assumption("That's how you win in this game!")),
            BooleanAdjective("a loss",
                definition = "node.final_node and node.score < 0",
                explanation = Assumption("That's how you lose in this game!")),
            BooleanAdjective("a draw",
                definition = "node.final_node and node.score == 0",
                explanation = Assumption("That's how you draw in this game!")),


            QuantitativePointerAdjective("score",
                definition = "node.score",

                explanation = ConditionalExplanation(
                    condition = If("leaf"),
                    explanation_if_true = ConditionalExplanation(
                        condition=If("a win"),
                        explanation_if_true=Possession("a win"),
                        explanation_if_false= ConditionalExplanation(
                            condition=If("a loss"),
                            explanation_if_true = Possession("a loss"),
                            explanation_if_false = Possession ("a draw")
                            )
                        ),
                    
                    explanation_if_false = ConditionalExplanation(
                        condition=If("fully searched"),

                        explanation_if_true = CompositeExplanation(
                            Assumption("We assume the opponent will do their best move and us our best move.", necessary=True),
                            RecursivePossession("as next move", any_stop_conditions = [If("as next move", "a win"), 
                                                                                        If("as next move", "a loss"), 
                                                                                        If("as next move", "a draw"), 
                                                                                        If("as next move", "the most forward in the future I looked"), 
                                                                                        If("as next move", "not fully searched")])),

                        explanation_if_false = ConditionalExplanation(
                            condition = If("as next move", "leaf"),

                            explanation_if_true = ConditionalExplanation(
                                condition=If("as next move", "a win"),
                                explanation_if_true=Possession("as next move", "a win"),
                                explanation_if_false= ConditionalExplanation(
                                    condition=If("as next move", "a loss"),
                                    explanation_if_true = Possession("as next move", "a loss"),
                                    explanation_if_false = Possession ("as next move", "a draw")
                                    )
                                ),

                            explanation_if_false = ConditionalExplanation(    
                                condition = If("opponent player turn"),

                                explanation_if_true = CompositeExplanation(
                                    Possession("as next possible move", explain_further=False),
                                    Comparison("as next possible move", "worse than the alternative coming from", "upperbound",
                                                forward_possessions_explanations=False),
                                    Assumption("The opponent can choose to do this move, or something even worse for us."),
                                    ),

                                explanation_if_false = CompositeExplanation(
                                    Possession("as next possible move", explain_further=False),
                                    Comparison("as next possible move", "better than the alternative coming from", "lowerbound",
                                                forward_possessions_explanations=False),
                                    Assumption("We could choose to do this move, or something even worse for the opponent."),                                                       
                                    ),
                                ),
                        ),
                    )
                ),
            ),                    

            BooleanAdjective("opponent player turn",
                definition = "not node.maximizing_player_turn"),

            BooleanAdjective("fully searched",
                definition = "node.fully_searched"),
            BooleanAdjective("not fully searched",
                definition = "not node.fully_searched"),

            PointerAdjective("as next move",
                definition = "node.score_child",
                explanation = ConditionalExplanation(
                    condition = If("fully searched"),
                    explanation_if_true = ConditionalExplanation(
                        condition = If("opponent player turn"),
                        explanation_if_true = CompositeExplanation(
                            Assumption("We assume the opponent will do their best move."),
                            Possession("as next move", "the best the opponent can do")),
                        explanation_if_false = CompositeExplanation(
                            Assumption("On our turn we take the maximum rated move."),
                            Possession("as next move", "the best"))
                        ),
                    explanation_if_false = Assumption("The move is legal.", implicit=True)
                    )
                ),
            
            PointerAdjective("as next possible move",
                definition = "node.score_child",
                explanation = Assumption("The move is legal.", implicit=True)),

            PointerAdjective("lowerbound",
                definition = "node.parent.beta"),

            PointerAdjective("upperbound",
                definition = "node.parent.alpha"),

            ComparisonAdjective("better or equal than", "score", ">="),
            ComparisonAdjective("worse or equal than", "score", "<="),

            ComparisonAdjective("better than the alternative coming from", "score", ">="),
            ComparisonAdjective("worse than the alternative coming from", "score", "<="),
        
            NodesGroupPointerAdjective("possible alternative moves",
                definition = "node.parent.children",
                excluding = "node"),

            MaxRankAdjective("the best", "better or equal than", "possible alternative moves",
                tactics = [CompactCollectiveConsequences(of_adjectives=["as next move", "as next possible move"])]),

            MaxRankAdjective("the best the opponent can do", "worse or equal than", "possible alternative moves",
                tactics = [CompactCollectiveConsequences(of_adjectives=["as next move", "as next possible move"])]),
        ]

        return adjectives
    


"""Further explanation to implement:

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