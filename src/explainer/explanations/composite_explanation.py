from .base import Explanation
from .simple_explanation import ComparisonNodesPropertyPossession

from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And

from typing import Any

class CompositeExplanation(Explanation):
    """Represents an explanation composed of multiple sub-explanations."""
    
    def __init__(self, *explanations: Explanation):
        super().__init__()
        """
        Initialize the CompositeExplanation.
        
        Args:
            *explanations: Variable number of Explanation objects to be combined.
        """
        self.explanations = explanations

    def _contextualize(self):
        for exp in self.explanations:
            exp.contextualize(self.explanation_of_adjective)

    def _explain(self, node: Any, other_node: Any = None) -> LogicalExpression:
        """
        Generate an explanation by combining all sub-explanations with AND.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A LogicalExpression representing the combination of all sub-explanations.
        """
        to_forward_explanations = []
        for exp in self.explanations:
            if exp is not None:
                if isinstance(exp, ComparisonNodesPropertyPossession):
                    to_forward_explanations.append((exp, node, other_node))
                else:
                    to_forward_explanations.append((exp, node))
        explanations = self.forward_multiple_explanations(*to_forward_explanations, no_increment = True)
        return And(*explanations)
    
    def implies(self) -> LogicalExpression:
        return And(*[exp.implies() for exp in self.explanations if exp is not None])