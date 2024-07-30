from .base import Explanation
from .simple_explanations import Possession

from src.explainer.propositional_logic import LogicalExpression, And, Or

from src.explainer.common.utils import apply_explanation_tactics

from typing import Any

class If(Possession):
    """
    Represents a condition based on an adjective's value.
    If provided with a pointer_adjective_name, the condition is based on the
    value stored at the pointer. If not, the condition is based on the self node.

    When not provided with a value, 
    the condition is simply checked as a static adjective (boolean)
    """

    def __init__(self, *args, value: Any = True):
        """
        Initialize the Condition.
        
        Usage:
            Condition("leaf")
            Conditon("backtracing child", "minoptimal")
            Condition("backtracing child", "score", value = 5)

        Args:
            *args: Either one or two string arguments.
                   If one argument: adjective_name
                   If two arguments: pointer_adjective_name, adjective_name
            value: Any, optional keyword-only argument
                   An optional value associated with the adjective explanation.
                   Must be specified as a keyword argument if provided.

            pointer_adjective_name: The name of the pointer adjective to the object to check.
            adjective_name: The name of the static adjective to check.
            value: The expected value of the adjective.
            
        """
        super().__init__(*args)
        self.value = value
    
    def implies(self, evaluation = True) -> LogicalExpression:
        """ Generates a proposition that contitutes the antecedent of an
        implication explaining why a certain adjective is attributed to
        a node. """

        adjective = self.framework.get_adjective(self.adjective_name)

        if not self.pointer_adjective_name: # the possession refers to the self node
            return adjective.implies(evaluation)

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)

            if self.explanation_of_adjective == pointer_adjective:
                # only forward the explanation without asking why this referred object
                implication = adjective.implies() # why the referred_object has this property?
            else:
                implication = And(
                    pointer_adjective.implies(), # why this referred_object?
                    adjective.implies(evaluation)) # why the referred_object has this property?
            return implication

    def evaluate(self, node: Any, explanation_tactics = None) -> bool:
        """
        Evaluate if the given node possess the given static adjective.
        
        Args:
            node: The node to evaluate.            
        
        Returns:
            True if the adjective's value matches the expected value, False otherwise.
        """

        if not self.pointer_adjective_name:        
            obj_under_evaluation = node
            
        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
            obj_under_evaluation = self.forward_evaluation(pointer_adjective, node)

        adjective = self.framework.get_adjective(self.adjective_name)
        evaluation = adjective.evaluate(obj_under_evaluation) == self.value
        return evaluation

class ConditionalExplanation(Explanation):
    """Represents an explanation that depends on a condition."""
    
    def __init__(self, condition: If, explanation_if_true: Explanation, explanation_if_false: Explanation):
        super().__init__()
        """
        Initialize the ConditionalExplanation.
        
        Args:
            condition: The condition to evaluate.
            explanation_if_true: The explanation to use when the condition is true.
            explanation_if_false: The explanation to use when the condition is false.
        """
        self.condition = condition
        self.explanation_if_true = explanation_if_true
        self.explanation_if_false = explanation_if_false

    def _contextualize(self):
        self.condition.contextualize(self.explanation_of_adjective)
        self.explanation_if_true.contextualize(self.explanation_of_adjective)
        self.explanation_if_false.contextualize(self.explanation_of_adjective)

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation based on the condition's evaluation.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A LogicalExpression representing the condition and the appropriate explanation.
        """
        if not node:
            return self.implies()
        condition_result = self.forward_evaluation(self.condition, node)

        if condition_result:
            explanations = self.forward_multiple_explanations(
                    (self.condition, node),
                    (self.explanation_if_true, node),
                    no_increment = True
                )
            explanation = And(*explanations)
        else:
            explanations = self.forward_multiple_explanations(
                    (self.condition, node),
                    (self.explanation_if_false, node),
                    no_increment = True
                )
            explanation = And(*explanations)

        return explanation

    def implies(self) -> LogicalExpression:
        explanation1 = And(
                        self.condition.implies(True), 
                        self.explanation_if_true.implies())
        explanation2 = And(
                        self.condition.implies(False), 
                        self.explanation_if_false.implies())
        return Or(explanation1, explanation2)
