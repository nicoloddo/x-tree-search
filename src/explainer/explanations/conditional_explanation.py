from .base import Explanation
from .fundamental_explanation import Possession

from src.explainer.propositional_logic import Postulate, LogicalExpression, And

from typing import Any

class If(Possession):
    """
    Represents a condition based on an adjective's value.
    If provided with a pointer_adjective_name, the condition is based on the
    value stored at the pointer. If not, the condition is based on the self node.

    When not provided with a value, 
    the condition is simply checked as a static adjective (boolean)
    """

    def __init__(self, *args, value: Any = True, explain_further=True, forward_possessions_explanations=True):
        """
        Initialize the Condition.
        
        Usage:
            Condition("leaf")
            Conditon("backtracing child", "minoptimal")
            Condition("backtracing child", "score", value = 5)

        :param args: Either one or two string arguments.
                     If one argument: adjective_name
                     If two arguments: pointer_adjective_name, adjective_name
        :type args: str
        :param value: An optional value associated with the adjective explanation, defaults to True.
                      Must be specified as a keyword argument if provided.
        :type value: Any, optional
        :param explain_further: Whether to explain the condition further, defaults to True.
        :type explain_further: bool, optional
        :param forward_possessions_explanations: Whether to forward possession explanations, defaults to True.
        :type forward_possessions_explanations: bool, optional

        pointer_adjective_name: The name of the pointer adjective to the object to check.
        adjective_name: The name of the static adjective to check.
        value: The expected value of the adjective.
        """
        super().__init__(*args)
        self.value = value
        self.explain_further=explain_further
        self.forward_possessions_explanations=forward_possessions_explanations

    def evaluate(self, node: Any, explanation_tactics = None) -> bool:
        """
        Evaluate if the given node possess the given static adjective.
        
        :param node: The node to evaluate.
        :type node: Any
        :param explanation_tactics: Explanation tactics, defaults to None.
        :type explanation_tactics: Any, optional
        :return: True if the adjective's value matches the expected value, False otherwise.
        :rtype: bool
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
    
    def __init__(self, *, condition: If, explanation_if_true: Explanation, explanation_if_false: Explanation, explicit_condition_statement: bool = False, explicit_condition_statement_if_true: bool = False, explicit_condition_statement_if_false: bool = False):
        """
        Initialize the ConditionalExplanation.
        
        :param condition: The condition to evaluate.
        :type condition: If
        :param explanation_if_true: The explanation to use when the condition is true.
        :type explanation_if_true: Explanation
        :param explanation_if_false: The explanation to use when the condition is false.
        :type explanation_if_false: Explanation
        :param explicit_condition_statement: Whether to explicitly state the condition, defaults to False.
        :type explicit_condition_statement: bool, optional
        :param explicit_condition_statement_if_true: Whether to explicitly state the condition if true, defaults to False.
        :type explicit_condition_statement_if_true: bool, optional
        :param explicit_condition_statement_if_false: Whether to explicitly state the condition if false, defaults to False.
        :type explicit_condition_statement_if_false: bool, optional
        """
        super().__init__()
        self.condition = condition
        self.explanation_if_true = explanation_if_true
        self.explanation_if_false = explanation_if_false
        self.explicit_condition_statement = explicit_condition_statement
        self.explicit_condition_statement_if_true = explicit_condition_statement_if_true
        self.explicit_condition_statement_if_false = explicit_condition_statement_if_false

    def _contextualize(self):
        self.condition.contextualize(self.explanation_of_adjective)
        self.explanation_if_true.contextualize(self.explanation_of_adjective)
        self.explanation_if_false.contextualize(self.explanation_of_adjective)
    
    def _decontextualize(self):
        self.condition.decontextualize()
        self.explanation_if_true.decontextualize()
        self.explanation_if_false.decontextualize()

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation based on the condition's evaluation.
        
        :param node: The node to explain.
        :type node: Any
        :return: A :class:`LogicalExpression` representing the condition and the appropriate explanation.
        :rtype: LogicalExpression
        """
        condition_result = self.forward_evaluation(self.condition, node)

        explicit_condition_statement = self.explicit_condition_statement or (condition_result==True and self.explicit_condition_statement_if_true) or (condition_result==False and self.explicit_condition_statement_if_false)

        if condition_result:
            if not explicit_condition_statement:
                explanation = self.forward_explanation(self.explanation_if_true, node, no_increment=True)
            else:
                explanations = self.forward_multiple_explanations(
                        (self.condition, node),
                        (self.explanation_if_true, node),
                        no_increment = True
                    )
                explanation = And(*explanations)
        else:
            if not explicit_condition_statement:
                explanation = self.forward_explanation(self.explanation_if_false, node, no_increment=True)
            else:
                explanations = self.forward_multiple_explanations(
                        (self.condition, node),
                        (self.explanation_if_false, node),
                        no_increment = True
                    )
                explanation = And(*explanations)

        return explanation