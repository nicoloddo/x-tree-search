from src.explainer.explainer import ArgumentativeExplainer
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import BooleanAdjective, PointerAdjective, QuantitativePointerAdjective, NodesGroupPointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective
from src.explainer.explanation import Possession, RecursivePossession, Assumption, Comparison, If, ConditionalExplanation, CompositeExplanation

from src.explainer.explanation_tactics import OnlyRelevantComparisons, SkipQuantitativeExplanations, CompactSameExplanations

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
            # Add your general framework explanation tactics here
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
            BooleanAdjective("final move",
                definition = "node.final_node"), # node is_leaf and not max_search_depth_reached
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
                skip_statement = True, # Don't say the score, pass directly to the explanation.
                # This framework is for users, and talking directly about scores is not understandable.
                # Let's instead put it in terms of next moves and win/loss/draw possibilities!
                
                # Explaining: why the move has this score?
                explanation = ConditionalExplanation(
                    condition = If("final move"),

                    # It's a final move: we say if it is a win, loss or draw
                    explanation_if_true = ConditionalExplanation(
                        condition=If("a win"), # Is it a win?
                        explanation_if_true=Possession("a win"),
                        explanation_if_false= ConditionalExplanation(
                            condition=If("a loss"), # It's not a win, is it a loss or a draw?
                            explanation_if_true = Possession("a loss"),
                            explanation_if_false = Possession ("a draw")
                            )
                        ),
                    
                    # That's not a final move
                    explanation_if_false = ConditionalExplanation(
                        condition=If("not worth exploring"),
                        
                        # The node has not been pruned, we have the full next future consequences list (until final moves or max search depth are reached)
                        explanation_if_false = CompositeExplanation(
                            Assumption("We assume the opponent will do their best move and us our best move.", necessary=True),
                            RecursivePossession("as next move", any_stop_conditions = [If("as next move", "a win"), # final move
                                                                                        If("as next move", "a loss"), # final move
                                                                                        If("as next move", "a draw"), # final move
                                                                                        If("as next move", "the most forward in the future I looked"), # max search depth
                                                                                        If("as next move", "not worth exploring")])), #TODO: What about this condition?

                        # The node has been pruned, we only have one children future consequence
                        explanation_if_true = ConditionalExplanation(
                            condition = If("as next move", "final move"), # Is the next move (the only one available) a final move?

                            # The only children of the move that we considered is actually a final move.
                            # In this case, we don't need to explain why the node was not worth exploring,
                            # users usually understand easily why this next possible move is not worth exploring when it is a final move.
                            # We simply can say if it is a win, loss or draw.
                            explanation_if_true = ConditionalExplanation(
                                condition=If("as next move", "a win"),
                                explanation_if_true=Possession("as next move", "a win"),
                                explanation_if_false= ConditionalExplanation(
                                    condition=If("as next move", "a loss"),
                                    explanation_if_true = Possession("as next move", "a loss"),
                                    explanation_if_false = Possession ("as next move", "a draw")
                                    )
                                ),

                            # Next move is not a final move, thus we need explain that the node was simply not worth exploring and why.
                            explanation_if_false = Possession("not worth exploring")
                        ),
                    )
                ),
            ),                    

            BooleanAdjective("opponent player turn",
                definition = "not node.maximizing_player_turn"),

            BooleanAdjective("not worth exploring",
                definition = "not node.fully_searched",
                explanation=ConditionalExplanation(    
                    condition = If("opponent player turn"),

                    explanation_if_true = CompositeExplanation(
                        Possession("as next possible move", explain_further=False),
                        Comparison("as next possible move", "worse than the alternative coming from", "upperbound",
                                    forward_possessions_explanations=False), # Do not forward explanations for "as next possible move" and "upperbound"
                        Assumption("The opponent can choose to do this move, or something even worse for us."),
                        ),

                    explanation_if_false = CompositeExplanation(
                        Possession("as next possible move", explain_further=False),
                        Comparison("as next possible move", "better than the alternative coming from", "lowerbound",
                                    forward_possessions_explanations=False), # Do not forward explanations for "as next possible move" and "lowerbound"
                        Assumption("We could choose to do this move, or something even worse for the opponent."),                                                       
                        ),
                    ),
            ),

            PointerAdjective("as next move",
                definition = "node.score_child",
                explanation = ConditionalExplanation(
                    condition = If("not worth exploring"),

                    # It was worth exploring (not pruned node)
                    explanation_if_false = ConditionalExplanation(
                        condition = If("opponent player turn"),
                        explanation_if_true = CompositeExplanation(
                            Assumption("We assume the opponent will do their best move."),
                            Possession("as next move", "the best the opponent can do")), # The next move is the best the opponent can do
                        explanation_if_false = CompositeExplanation(
                            Assumption("On our turn we take the maximum rated move."),
                            Possession("as next move", "the best"))
                        ),
                    
                    # It was not worth exploring, we just took the first move
                    explanation_if_true = Assumption("The move is legal.", implicit=True)
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
                tactics = [
                    CompactSameExplanations(
                        from_adjectives=["as next move", 
                                       "as next possible move"],
                        same_if_equal_keys=[('evaluation', ['id_length', 'last_move_id'])]
                    ),
                    CompactSameExplanations(
                        from_adjectives=["not worth exploring"],
                        same_if_equal_keys=['evaluation']
                    )
                ]
            ),

            MaxRankAdjective("the best the opponent can do", "worse or equal than", "possible alternative moves",
                tactics = [
                    CompactSameExplanations(
                        from_adjectives=["as next move", 
                                       "as next possible move"],
                        same_if_equal_keys=[('evaluation', ['id_length', 'last_move_id'])]
                    ),
                    CompactSameExplanations(
                        from_adjectives=["not worth exploring"],
                        same_if_equal_keys=['evaluation']
                    )
                ]
            )
        ]

        return adjectives