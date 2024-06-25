from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from src.explainer.propositional_logic import Proposition, And, Or, Implies, Not

class Explanation(ABC):
    """
    Abstract base class for all types of explanations.
    Explanations provide the reasoning behind why a node has a certain adjective.
    """
    @abstractmethod
    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate a propositional logic explanation for the given node.

        Args:
            node: The node to explain.
            context: Additional context information for the explanation.

        Returns:
            A Proposition representing the explanation.
        """
        pass

class AdjectiveExplanation(Explanation):
    """
    Represents an explanation that refers to an adjective of a specific child node,
    where the child is determined by a pointer adjective.
    """

    def __init__(self, adjective_name: str, child_pointer_name: str):
        """
        Initialize the AdjectiveExplanation.

        Args:
            adjective_name: The name of the adjective to explain.
            child_pointer_name: The name of the pointer adjective that selects the relevant child.
        """
        self.adjective_name = adjective_name
        self.child_pointer_name = child_pointer_name

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate a propositional logic explanation by redirecting to explain_adjective for the selected child.

        Args:
            node: The parent node.
            context: Additional context for the explanation, including the explainer.

        Returns:
            A Proposition representing the explanation of the specified adjective for the selected child.
        """
        explainer = context.get('explainer')
        if not explainer:
            raise ValueError("Explainer not found in context.")
        
        # Get the child using the pointer adjective
        child_pointer = explainer.framework.get_adjective(self.child_pointer_name)
        child = child_pointer.evaluate(node)
        
        # Explain the child pointer
        child_pointer_explanation = explainer.explain_adjective(node, self.child_pointer_name)
        
        # Explain the adjective for the child
        child_adjective_explanation = explainer.explain_adjective(child, self.adjective_name)
        
        return And(
            child_pointer_explanation,
            Implies(
                Proposition(f"{self.child_pointer_name} points to {child}"),
                And(
                    Proposition(f"{node} takes value from {child}"),
                    child_adjective_explanation
                )
            )
        )

class AssumptionExplanation(Explanation):
    """
    Represents an explanation that is based on an assumption.
    This is the simplest form of explanation, used when no further reasoning is needed.
    """
    def __init__(self, description: str):
        """
        Initialize the assumption explanation.

        Args:
            description: A string describing the assumption.
        """
        self.description = description

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate a propositional logic explanation based on the assumption.

        Args:
            node: The node to explain (not used for assumptions).
            context: Additional context (not used for assumptions).

        Returns:
            A Proposition representing the assumption.
        """
        return Proposition(self.description)

class ConditionalExplanation(Explanation):
    """
    Represents an explanation that depends on a condition.
    Different explanations are provided based on whether the condition is true or false.
    """
    def __init__(self, condition: Callable[[Any], bool], true_explanation: Explanation, false_explanation: Explanation):
        """
        Initialize the conditional explanation.

        Args:
            condition: A function that takes a node and returns a boolean.
            true_explanation: The explanation to use when the condition is true.
            false_explanation: The explanation to use when the condition is false.
        """
        self.condition = condition
        self.true_explanation = true_explanation
        self.false_explanation = false_explanation

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate a propositional logic explanation based on the condition.

        Args:
            node: The node to explain.
            context: Additional context for the explanation.

        Returns:
            A Proposition representing the appropriate explanation based on the condition.
        """
        if self.condition(node):
            return self.true_explanation.explain(node, context)
        else:
            return self.false_explanation.explain(node, context)

class CompositeExplanation(Explanation):
    """
    Represents an explanation composed of multiple sub-explanations.
    All sub-explanations are combined using logical AND.
    """
    def __init__(self, *explanations: Explanation):
        """
        Initialize the composite explanation.

        Args:
            *explanations: Variable number of Explanation objects to be combined.
        """
        self.explanations = explanations

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate a propositional logic explanation by combining all sub-explanations.

        Args:
            node: The node to explain.
            context: Additional context for the explanation.

        Returns:
            A Proposition representing the combination of all sub-explanations.
        """
        return And(*[exp.explain(node, context) for exp in self.explanations])
