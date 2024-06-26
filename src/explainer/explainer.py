from typing import Any

from src.explainer.propositional_logic import Implies, Not
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import RankingAdjective

class ArgumentativeExplainer:
    """
    Generates explanations based on the argumentation framework.
    The nodes of the tree to explain need to have the following parameters:
        - children
        - parent
    It is suggested to provide a __str__(self) method to print the nodes.
    If the tree nodes do not have them, it is mandatory to create an
    interfacing layer between the tree and the explainer for the Explainer.
    """
    
    def __init__(self, framework: ArgumentationFramework):
        """
        Initialize the ArgumentativeExplainer.
        
        Args:
            framework: The ArgumentationFramework to use for explanations.
        """
        self.framework = framework

    def explain_adjective(self, node: Any, adjective_name: str, comparison_node: Any = None) -> Implies:
        """
        Generate a propositional logic explanation for why a node has a specific adjective.
        
        Args:
            node: The node to explain.
            adjective_name: The name of the adjective to explain.
            comparison_node: The other node involved in a comparison (if it is a comparison)
        
        Returns:
            A Implies implication representing the explanation of the adjective's affirmation.
        
        Raises:
            KeyError: If no adjective with the given name is found.
        """
        adjective = self.framework.get_adjective(adjective_name)
        context = {"explainer": self, "node": node}
        
        if not comparison_node: # The adjective is not comparative
            truth = adjective.evaluate(node)
            explanation = adjective.explanation(node, context)
            affirmation = adjective.affirm(node, not truth)
        
        else:
            if not isinstance(adjective, RankingAdjective):
                raise ValueError("Comparison explanations are possible only with RankingAdjectives.")
            truth = adjective.evaluate(node, comparison_node)
            explanation = adjective.explanation(node, comparison_node, context, not truth)
            affirmation = adjective.affirm(node, comparison_node, not truth)

        return Implies(explanation, affirmation) 


    def query_explanation(self, node: Any, query: str) -> Implies:
        pass
        """
        Generate an explanation for a specific query about a node's adjective.
        
        Args:
            node: The node to explain.
            query: A string query in the format "Why does [node] have [adjective]?"
        
        Returns:
            An implication representing the explanation, or an error message for invalid queries.
        """
        parts = query.lower().split()
        if len(parts) >= 4 and parts[0] == "why" and parts[1] == "does":
            adjective_name = parts[-1].rstrip("?")
            return self.explain_adjective(node, adjective_name)
        else:
            return #Implies("Invalid query format. Please use 'Why does [node] have [adjective]?'")
