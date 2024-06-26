from enum import Enum
from typing import Any, Callable, Dict
from abc import ABC, abstractmethod

from src.explainer.explanation import Explanation, AssumptionExplanation, ComparisonAssumptionExplanation

class AdjectiveType(Enum):
    """Enum for different types of adjectives."""
    STATIC = 1  # Represents boolean attributes of nodes
    POINTER = 2  # Represents attributes that point to specific values or objects
    RANKING = 3  # Represents attributes used for comparing nodes

class Adjective(ABC):
    """Abstract base class for all types of adjectives."""
    
    def __init__(self, name: str, adjective_type: AdjectiveType, explanation: Explanation):
        """
        Initialize the Adjective.
        
        Args:
            name: The name of the adjective.
            adjective_type: The type of the adjective (STATIC, POINTER, or RANKING).
            explanation: A callable that takes a node and context and returns a Proposition.
        """
        self.name = name
        self.type = adjective_type
        self.explanation = explanation

    @abstractmethod
    def evaluate(self, node: Any) -> Any:
        """
        Evaluate the adjective for a given node.
        
        Args:
            node: The node to evaluate.
        
        Returns:
            The value of the adjective for the given node.
        """
        pass

class StaticAdjective(Adjective):
    """Represents a static (boolean) adjective."""
    
    def __init__(self, name: str, condition: Callable[[Any], bool], explanation: Explanation = None):
        """
        Initialize the StaticAdjective.
        
        Args:
            name: The name of the adjective.
            condition: A function that takes a node and returns a boolean.
            explanation: A callable that takes a node and context and returns a Proposition.
        """
        explanation = explanation or AssumptionExplanation(f"Considering your definition of {name}")
        explanation = explanation.explain
        super().__init__(name, AdjectiveType.STATIC, explanation)
        self.condition = condition

    def evaluate(self, node: Any) -> bool:
        """Evaluate the static adjective for a given node."""
        return self.condition(node)

    def affirm(self, node: Any, negation=False) -> str:
        """ Printable affirmation of the node regarding the adjective """
        evaluation_result = " not" if negation else ""
        return f"{node} is{evaluation_result} {self.name}"

class PointerAdjective(Adjective):
    """Represents a pointer adjective that references a specific attribute or object."""
    
    def __init__(self, name: str, getter: Callable[[Any], Any], explanation: Explanation = None):
        """
        Initialize the PointerAdjective.
        
        Args:
            name: The name of the adjective.
            getter: A function that takes a node and returns the pointed value.
            explanation: A callable that takes a node and context and returns a Proposition.
        """
        explanation = explanation or AssumptionExplanation(f"Considering your definition of {name}")
        explanation = explanation.explain
        super().__init__(name, AdjectiveType.POINTER, explanation)
        self.getter = getter

    def evaluate(self, node: Any) -> Any:
        """Evaluate the pointer adjective for a given node."""
        return self.getter(node)

    def affirm(self, node: Any, negation=False) -> str:
        """ Printable affirmation of the node regarding the adjective """
        # The negation here does not matter
        return f"{node} has {self.name} = {self.evaluate(node)}"

class RankingAdjective(Adjective):
    """Represents a ranking adjective used for comparing nodes."""
    
    def __init__(self, name: str, pointer_adjective_name: str, operator: str):
        """
        Initialize the RankingAdjective.
        
        Args:
            name: The name of the adjective.
            pointer_adjective_name: The name of the pointer adjective to use for comparison.
            comparison_operator: A function that compares two values and returns a boolean.
        """
        explanation = ComparisonAssumptionExplanation(name, pointer_adjective_name, operator)
        explanation = explanation.explain
        super().__init__(name, AdjectiveType.RANKING, explanation)
        self.pointer_adjective_name = pointer_adjective_name

        # Validate the operator to ensure it's safe and expected
        if operator not in ['>', '<', '==', '!=', '>=', '<=']:
            raise ValueError("Invalid operator")
        # Construct and return the lambda function
        else:
            self.comparison_operator = eval(f"lambda x, y: x {operator} y")

        self.operator = operator

    def evaluate(self, node1: Any, node2: Any) -> bool:
        """
        Evaluate the ranking between two nodes.
        
        Args:
            node1: The first node to compare.
            node2: The second node to compare.
        
        Returns:
            A boolean indicating whether node1 ranks higher than node2.
        """
        value1 = getattr(node1, self.pointer_adjective_name)
        value2 = getattr(node2, self.pointer_adjective_name)
        return self.comparison_operator(value1, value2)

    def affirm(self, node1: Any, node2: Any, negation=False) -> str:
        """ Printable affirmation of the node regarding the adjective """
        evaluation_result = "not " if negation else ""
        return f"{node1} {evaluation_result}{self.name} than {node2}"

def create_comparison_lambda(operator):
    try:
        # Validate the operator to ensure it's safe and expected
        if operator not in ['>', '<', '==', '!=', '>=', '<=']:
            raise ValueError("Invalid operator")
        # Construct and return the lambda function
        return eval(f"lambda x, y: x {operator} y")
    except SyntaxError:
        raise ValueError("Invalid syntax for operator.")
