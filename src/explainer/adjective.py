from enum import Enum
from typing import Any, Callable, Dict
from abc import ABC, abstractmethod

from src.explainer.propositional_logic import Proposition
from src.explainer.explanation import Explanation, AssumptionExplanation

class AdjectiveType(Enum):
    """Enum for different types of adjectives."""
    STATIC = 1  # Represents boolean attributes of nodes
    POINTER = 2  # Represents attributes that point to specific values or objects
    POINTER_RANKING = 3  # Represents attributes used for comparing nodes

class Adjective(ABC):
    """
    Abstract base class for all types of adjectives.
    Adjectives represent properties or attributes of nodes in the search tree.
    """
    def __init__(self, name: str, adjective_type: AdjectiveType, explanation: Explanation):
        """
        Initialize the adjective.

        Args:
            name: The name of the adjective.
            adjective_type: The type of the adjective (STATIC, POINTER, or POINTER_RANKING).
            explanation: The explanation for why a node has this adjective.
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

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate a propositional logic explanation for why the node has this adjective.

        Args:
            node: The node to explain.
            context: Additional context for the explanation.

        Returns:
            A Proposition representing the explanation.
        """
        return self.explanation.explain(node, context)

class StaticAdjective(Adjective):
    """
    Represents a static (boolean) adjective.
    Static adjectives are explained by their condition, which is treated as an assumption.
    """
    def __init__(self, name: str, condition: Callable[[Any], bool]):
        """
        Initialize the static adjective.

        Args:
            name: The name of the adjective.
            condition: A function that takes a node and returns a boolean.
        """
        super().__init__(name, AdjectiveType.STATIC, AssumptionExplanation(f"{name} is defined by its condition"))
        self.condition = condition

    def evaluate(self, node: Any) -> bool:
        """
        Evaluate the static adjective for a given node.

        Args:
            node: The node to evaluate.

        Returns:
            A boolean indicating whether the node has this adjective.
        """
        return self.condition(node)

class PointerAdjective(Adjective):
    """
    Represents a pointer adjective that references a specific attribute or object.
    """
    def __init__(self, name: str, getter: Callable[[Any], Any], explanation: Explanation = None):
        """
        Initialize the pointer adjective.

        Args:
            name: The name of the adjective.
            getter: A function that takes a node and returns the value of the adjective.
            explanation: An optional explanation for the adjective (defaults to a simple assumption).
        """
        super().__init__(name, AdjectiveType.POINTER, explanation or AssumptionExplanation(f"{name} is assigned by default"))
        self.getter = getter

    def evaluate(self, node: Any) -> Any:
        """
        Evaluate the pointer adjective for a given node.

        Args:
            node: The node to evaluate.

        Returns:
            The value of the adjective for the given node.
        """
        return self.getter(node)

class PointerRankingAdjective(Adjective):
    """
    Represents a pointer ranking adjective used for comparing nodes.
    This adjective automatically creates related max, min, and pointer adjectives.
    """
    def __init__(self, name: str, pointer_name: str, compare: Callable[[Any, Any], bool]):
        """
        Initialize the pointer ranking adjective.

        Args:
            name: The name of the adjective.
            pointer_name: The name of the related pointer adjective.
            compare: A function that takes two nodes and returns a boolean indicating their relative ranking.
        """
        super().__init__(name, AdjectiveType.POINTER_RANKING, AssumptionExplanation(f"{name} is defined by its comparison function"))
        self.pointer_name = pointer_name
        self.compare = compare
        self.max_name = f"max_{name}"
        self.min_name = f"min_{name}"

    def evaluate(self, node1: Any, node2: Any) -> bool:
        """
        Evaluate the ranking between two nodes.

        Args:
            node1: The first node to compare.
            node2: The second node to compare.

        Returns:
            A boolean indicating whether node1 ranks higher than node2.
        """
        return self.compare(node1, node2)

    def create_max_adjective(self) -> StaticAdjective:
        """
        Create a static adjective representing the maximum condition.

        Returns:
            A StaticAdjective for the maximum condition.
        """
        def max_condition(node: Any) -> bool:
            return all(self.evaluate(node, sibling) for sibling in node.parent.children if sibling != node)
        return StaticAdjective(self.max_name, max_condition)

    def create_min_adjective(self) -> StaticAdjective:
        """
        Create a static adjective representing the minimum condition.

        Returns:
            A StaticAdjective for the minimum condition.
        """
        def min_condition(node: Any) -> bool:
            return all(self.evaluate(sibling, node) for sibling in node.parent.children if sibling != node)
        return StaticAdjective(self.min_name, min_condition)

    def create_pointer_adjective(self) -> PointerAdjective:
        """
        Create a pointer adjective based on this ranking adjective.

        Returns:
            A PointerAdjective for the value being compared.
        """
        def getter(node: Any) -> Any:
            return getattr(node, self.pointer_name)
        return PointerAdjective(self.pointer_name, getter)