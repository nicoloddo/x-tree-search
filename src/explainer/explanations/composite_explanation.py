from .base import Explanation
from src.explainer.common.utils import AdjectiveType
from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And
from typing import Any

class CompositeExplanation(Explanation):
    """
    Represents an explanation composed of multiple sub-explanations.

    This class combines multiple :class:`Explanation` objects to create a composite
    explanation. It handles the contextualization, decontextualization, and 
    explanation generation for all sub-explanations.
    """
    
    def __init__(self, *explanations: Explanation):
        """
        Initialize the CompositeExplanation with multiple sub-explanations.

        :param explanations: Variable number of :class:`Explanation` objects to be combined.
        :type explanations: Explanation
        """
        super().__init__()
        self.explanations = explanations

    def _contextualize(self):
        """
        Contextualize all sub-explanations.

        This method applies the contextualization process to each sub-explanation
        using the composite explanation's explanation_of_adjective.
        """
        for exp in self.explanations:
            exp.contextualize(self.explanation_of_adjective)
        
    def _decontextualize(self):
        """
        Decontextualize all sub-explanations.

        This method removes the context from each sub-explanation.
        """
        for exp in self.explanations:
            exp.decontextualize()

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generate a composite explanation by combining all sub-explanations with AND.

        This method creates an explanation for the given node by combining
        the results of all sub-explanations using a logical AND operation.

        :param node: The node to explain.
        :type node: Any
        :return: A :class:`LogicalExpression` representing the combination of all sub-explanations.
        :rtype: LogicalExpression
        """
        to_forward_explanations = []
        for exp in self.explanations:
            if exp is not None:
                to_forward_explanations.append((exp, node))
        
        explanations = self.forward_multiple_explanations(*to_forward_explanations, no_increment=True)
        return And(*explanations)