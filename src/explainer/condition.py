from abc import ABC, abstractmethod
from typing import Any, Dict

class Condition(ABC):
    """Represents a condition based on an adjective's value."""
    
    @abstractmethod
    def evaluate(self, node: Any, context: Dict[str, Any]) -> bool:
        """Evaluates the condition for the given node"""
        pass

class Condition(Condition):
    """
    Represents a condition.
    If provided with a pointer_adjective_name, the condition is based on the
    value stored at the pointer. If not, the condition is based on the self node.

    When not provided with a value, 
    the condition is simply checked as a static adjective (boolean)
    """

    def __init__(self, adjective_name: str = None, pointer_adjective_name: str = None, *, value: Any = True):
        """
        Initialize the Condition.
        
        Args:
            adjective_name: The name of the static adjective to check.
            value: The expected value of the adjective.
            pointer_adjective_name: The name of the pointer adjective to the object to check.
        """
        self.adjective_name = adjective_name
        self.pointer_adjective_name = pointer_adjective_name
        self.value = value

    def evaluate(self, node: Any, context: Dict[str, Any]) -> bool:
        """
        Evaluate if the given node possess the given static adjective.
        
        Args:
            node: The node to evaluate.
            context: Additional context, including the explainer.
        
        Returns:
            True if the adjective's value matches the expected value, False otherwise.
        """

        explainer = context['explainer'] 

        if not self.pointer_adjective_name:        
            obj_under_evaluation = node
            
        else:
            pointer_adjective = explainer.framework.get_adjective(self.pointer_adjective_name)
            obj_under_evaluation = pointer_adjective.evaluate(node)

        adjective = explainer.framework.get_adjective(self.adjective_name)
        return adjective.evaluate(obj_under_evaluation) == self.value