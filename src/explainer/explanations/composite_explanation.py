from .base import Explanation
from src.explainer.common.utils import AdjectiveType

from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And

from typing import Any

class CompositeExplanation(Explanation):
    """Represents an explanation composed of multiple sub-explanations."""
    
    def __init__(self, *explanations: Explanation):
        """
        Initialize the CompositeExplanation.
        
        Args:
            *explanations: Variable number of Explanation objects to be combined.
        """
        super().__init__()
        self.explanations = explanations

    def _contextualize(self):
        for exp in self.explanations:
            exp.contextualize(self.explanation_of_adjective)
        
    def _decontextualize(self):
        for exp in self.explanations:
            exp.decontextualize()

    def _explain(self, node: Any) -> LogicalExpression:
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
                to_forward_explanations.append((exp, node))
        explanations = self.forward_multiple_explanations(*to_forward_explanations, no_increment = True)
        return And(*explanations)