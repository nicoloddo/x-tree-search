from src.explainer.explainer import ArgumentativeExplainer
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import BooleanAdjective, PointerAdjective, QuantitativePointerAdjective, NodesGroupPointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective
from src.explainer.adjective import COMPARISON_AUXILIARY_ADJECTIVE
from src.explainer.explanation import Possession, RecursivePossession, Assumption, Comparison, If, ConditionalExplanation, CompositeExplanation

from src.explainer.explanation_tactics import OnlyRelevantComparisons, SkipQuantitativeExplanations, CompactComparisonsWithSameExplanation

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
        explainer.configure_settings(settings)
        
        # Create argumentation framework
        highlevel_framework = ArgumentationFramework(
            refer_to_nodes_as='move',
            adjectives=adjectives,
            main_explanation_adjective='the best',
            tactics=tactics,
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
                explanation = Assumption("These are the rules!")),
            BooleanAdjective("a loss",
                definition = "node.final_node and node.score < 0",
                explanation = Assumption("These are the rules!")),
            BooleanAdjective("a draw",
                definition = "node.final_node and node.score == 0",
                explanation = Assumption("These are the rules!")),


            QuantitativePointerAdjective("score",
                definition = "node.readable_score",
                skip_statement = True, # Don't say the score, pass directly to the explanation.
                # This framework is for users, and talking directly about scores is not understandable.
                # Let's instead put it in terms of next moves and win/loss/draw possibilities!
                
                # Explaining: why the move has this score?
                explanation = ConditionalExplanation(
                    condition = If("possession", "final move"),

                    # It's a final move: we say if it is a win, loss or draw
                    explanation_if_true = ConditionalExplanation(
                        condition=If("possession", "a win"), # Is it a win?
                        explanation_if_true=Possession("a win"),
                        explanation_if_false= ConditionalExplanation(
                            condition=If("possession", "a loss"), # It's not a win, is it a loss or a draw?
                            explanation_if_true = Possession("a loss"),
                            explanation_if_false = Possession ("a draw")
                            )
                        ),
                    
                    # That's not a final move
                    explanation_if_false = ConditionalExplanation(
                        condition = If("possession", "the most forward in the future I looked"),

                        explanation_if_true = CompositeExplanation(
                            Possession("the most forward in the future I looked"),
                            Assumption("when I can't look further in the future, my evaluation of a move is qualitative, only based on the board position after it"),
                        ),
                    
                        explanation_if_false = ConditionalExplanation(
                            condition=If("possession", "not worth exploring after checking the first possible next move"),
                            
                            # The node has not been pruned, we have the full next future consequences list (until final moves or max search depth are reached)
                            explanation_if_false = Possession("as future position after few moves"),

                            # The node has been pruned, we only have one children future consequence
                            explanation_if_true = ConditionalExplanation(
                                condition = If("possession", "as next move", "final move"), # Is the next move (the only one available) a final move?

                                # The only children of the move that we considered is actually a final move.
                                # In this case, we don't need to explain why the node was not worth exploring after checking the first possible next move,
                                # users usually understand easily why this next possible move is not worth exploring after checking the first possible next move when it is a final move.
                                # We simply can say if it is a win, loss or draw.
                                explanation_if_true = ConditionalExplanation(
                                    condition=If("possession", "as next move", "a win"),
                                    explanation_if_true=Possession("as next move", "a win"),
                                    explanation_if_false= ConditionalExplanation(
                                        condition=If("possession", "as next move", "a loss"),
                                        explanation_if_true = Possession("as next move", "a loss"),
                                        explanation_if_false = Possession ("as next move", "a draw")
                                        )
                                    ),

                                # Next move is not a final move, thus we need explain that the node was simply not worth exploring after checking the first possible next move and why.
                                explanation_if_false = CompositeExplanation(
                                    Possession("as next possible move"),
                                    Possession("not worth exploring after checking the first possible next move"),
                                )
                            ),
                        )
                    )
                ),
            ),                    

            BooleanAdjective("opponent player turn",
                definition = "not node.maximizing_player_turn"),

            BooleanAdjective("not worth exploring after checking the first possible next move",
                # Please use Possession("as next possible move") together with this explanation.
                definition = "not node.fully_searched",
                explanation=ConditionalExplanation(    
                    condition = If("possession", "opponent player turn"),

                    explanation_if_true = CompositeExplanation(
                        Assumption("The opponent can choose to do this possible next move, or something even worse for me."),
                        ConditionalExplanation(
                            condition = If("comparison", "as next possible move", "worse for me than", "upperbound"),
                            explanation_if_true = Comparison("as next possible move", "already worse for me than the alternative coming after", "upperbound",
                                    forward_possessions_explanations=False), # Do not forward explanations for "as next possible move" and "upperbound"
                            explanation_if_false = Comparison("as next possible move", "already equal to the alternative coming after", "upperbound",
                                    forward_possessions_explanations=False)
                        ),
                    ),

                    explanation_if_false = CompositeExplanation(
                        Possession("as next possible move", explain_further=False),
                        Assumption("We could choose to do this move, or something even worse for the opponent."),  
                        ConditionalExplanation(
                            condition = If("comparison", "as next possible move", "better for me than", "lowerbound"),
                            explanation_if_true = Comparison("as next possible move", "already better for me than the alternative coming after", "lowerbound",
                                    forward_possessions_explanations=False), # Do not forward explanations for "as next possible move" and "lowerbound"  
                            explanation_if_false = Comparison("as next possible move", "already equal to the alternative coming after", "lowerbound",
                                    forward_possessions_explanations=False)
                        ),
                    ),
                ),
            ),

            PointerAdjective("as next move",
                definition = "node.score_child",
                explanation = ConditionalExplanation(
                    condition = If("possession", "not worth exploring after checking the first possible next move"),

                    # It was worth exploring (not pruned node)
                    explanation_if_false = ConditionalExplanation(
                        condition = If("possession", "opponent player turn"),
                        explanation_if_true = CompositeExplanation(
                            Assumption("We assume the opponent will do their best move."),
                            Possession("as next move", "the best the opponent can do")), # The next move is the best the opponent can do
                        explanation_if_false = CompositeExplanation(
                            Assumption("On our turn we take the maximum rated move."),
                            Possession("as next move", "the best for me"))
                        ),
                    
                    # It was not worth exploring after checking the first possible next move, we just took the first move
                    explanation_if_true = Assumption("The move is legal.", implicit=True)
                    )
                ),
            
            PointerAdjective("as future position after few moves",
                definition = "node.deep_score_child",
                explanation = CompositeExplanation(
                    Assumption("We assume the opponent will do their best move and us our best move.", necessary=True),
                    RecursivePossession("as next move", any_stop_conditions = [If("possession", "as next move", "a win"), # final move
                                                                                If("possession", "as next move", "a loss"), # final move
                                                                                If("possession", "as next move", "a draw"), # final move
                                                                                If("possession", "as next move", "the most forward in the future I looked")]) # max search depth
                    )
            ),
            
            PointerAdjective("as next possible move",
                definition = "node.score_child",
                explanation = Assumption("The move is legal.", implicit=True)),

            PointerAdjective("lowerbound",
                definition = "node.parent.beta"),

            PointerAdjective("upperbound",
                definition = "node.parent.alpha"),

            ComparisonAdjective("better for me than", "score", ">",
                                explain_with_adj_if=(If("comparison", "equal to", COMPARISON_AUXILIARY_ADJECTIVE), "equal to")),
            ComparisonAdjective("worse for me than", "score", "<",
                                explain_with_adj_if=(If("comparison", "equal to", COMPARISON_AUXILIARY_ADJECTIVE), "equal to")),
            ComparisonAdjective("equal to", "score", "=="),
            ComparisonAdjective("at least equal to", "score", "=="),

            ComparisonAdjective("already better for me than the alternative coming after", "score", ">"),
            ComparisonAdjective("already worse for me than the alternative coming after", "score", "<"),
            ComparisonAdjective("already equal to the alternative coming after", "score", "=="),
        
            NodesGroupPointerAdjective("possible alternative moves",
                definition = "node.parent.children",
                excluding = "node"),

            MaxRankAdjective("the best", ["better for me than", "at least equal to"], "possible alternative moves",
                explain_with_adj_if = (If("possession", "opponent player turn"), "the best for me", "the best the opponent can do"),
            ),

            MaxRankAdjective("the best for me", ["better for me than", "at least equal to"], "possible alternative moves",
                explain_with_adj_if = (If("possession", "opponent player turn", value=False), "the best the opponent can do"),
                tactics = [
                    CompactComparisonsWithSameExplanation(
                        from_adjectives=["as next move", 
                                       "as next possible move"],
                        same_if_equal_keys=[('evaluation', ['depth', 'last_move_id'])],
                        also_compact_adjectives = ["not worth exploring after checking the first possible next move"]
                    )
                ]
            ),

            MaxRankAdjective("the best the opponent can do", ["worse for me than", "at least equal to"], "possible alternative moves",
                explain_with_adj_if = (If("possession", "opponent player turn"), "the best for me"),
                tactics = [
                    CompactComparisonsWithSameExplanation(
                        from_adjectives=["as next move", 
                                       "as next possible move"],
                        same_if_equal_keys=[('evaluation', ['depth', 'last_move_id'])],
                        also_compact_adjectives = ["not worth exploring after checking the first possible next move"]
                    )
                ]
            )
        ]

        return adjectives