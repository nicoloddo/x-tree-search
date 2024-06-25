from typing import Any

from src.explainer.propositional_logic import Proposition, And, Or, Implies, Not
from src.explainer.framework import ArgumentationFramework

class ArgumentativeExplainer:
    """
    Class for generating explanations and handling queries based on the argumentation framework.
    This class focuses on the explanation generation process.
    """
    def __init__(self, framework: ArgumentationFramework):
        """
        Initialize the ArgumentativeExplainer.

        Args:
            framework: The ArgumentationFramework to use for explanations.
        """
        self.framework = framework

    def explain_adjective(self, node: Any, adjective_name: str) -> Proposition:
        """
        Generate a propositional logic explanation for why a node has a specific adjective.

        Args:
            node: The node to explain.
            adjective_name: The name of the adjective to explain.

        Returns:
            A Proposition representing the explanation.

        Raises:
            ValueError: If no adjective with the given name is found.
        """
        adjective = self.framework.get_adjective(adjective_name)
        context = {"explainer": self, "node": node}
        return adjective.explain(node, context)

    def query_explanation(self, node: Any, query: str) -> Proposition:
        """
        Generate an explanation for a specific query about a node's adjective.

        Args:
            node: The node to explain.
            query: A string query in the format "Why does [node] have [adjective]?"

        Returns:
            A Proposition representing the explanation, or an error message for invalid queries.
        """
        parts = query.lower().split()
        if len(parts) >= 4 and parts[0] == "why" and parts[1] == "does":
            adjective_name = parts[-1].rstrip("?")
            return self.explain_adjective(node, adjective_name)
        else:
            return Proposition("Invalid query format. Please use 'Why does [node] have [adjective]?'")