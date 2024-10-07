from .base import Explanation
from .fundamental_explanation import Possession, Comparison

from src.explainer.propositional_logic import Postulate, LogicalExpression, And

from typing import Any

class If(Explanation):
    """
    Represents a condition based on an adjective's value.
    Can be used for both possession and comparison conditions.
    """

    def __init__(self, condition_type, *args, value: Any = True, explain_further=True, forward_possessions_explanations=False):
        """
        Initialize the If condition.
        
        Usage:
            If("possession", "leaf")
            If("possession", "backtracing child", "minoptimal")
            If("possession", "backtracing child", "score", value=5)
            If("comparison", "score", "better than", "other_node_score")

        :param condition_type: Type of condition, either "possession" or "comparison"
        :type condition_type: str
        :param args: Arguments for the condition (see usage examples)
        :type args: str
        :param value: An optional value for possession conditions, defaults to True
        :type value: Any, optional
        :param explain_further: Whether to explain the condition further, defaults to True
        :type explain_further: bool, optional
        :param forward_possessions_explanations: Whether to forward possession explanations, defaults to True
        :type forward_possessions_explanations: bool, optional
        """
        super().__init__()
        self.condition_type = condition_type
        self.value = value
        self.explain_further = explain_further
        self.forward_possessions_explanations = forward_possessions_explanations

        if condition_type == "possession":
            self.condition = Possession(*args, explain_further=explain_further, forward_possessions_explanations=forward_possessions_explanations)
        elif condition_type == "comparison":
            self.condition = Comparison(*args, explain_further=explain_further, forward_possessions_explanations=forward_possessions_explanations)
        else:
            raise ValueError("Invalid condition_type. Must be either 'possession' or 'comparison'.")

    def _contextualize(self):
        self.condition.contextualize(self.explanation_of_adjective)
    
    def _decontextualize(self):
        self.condition.decontextualize()

    def evaluate(self, node: Any, explanation_tactics = None) -> bool:
        """
        Evaluate the condition for the given node.
        
        :param node: The node to evaluate
        :type node: Any
        :param other_nodes: Additional nodes for comparison conditions, defaults to None
        :type other_nodes: Any, optional
        :return: True if the condition is met, False otherwise
        :rtype: bool
        """
        if self.condition_type == "possession":
            obj_under_evaluation = node if not self.condition.pointer_adjective_name else self.forward_evaluation(self.framework.get_adjective(self.condition.pointer_adjective_name), node)
            adjective = self.framework.get_adjective(self.condition.adjective_name)
            return adjective.evaluate(obj_under_evaluation) == self.value
        elif self.condition_type == "comparison":
            obj1 = node if self.condition.obj1_pointer_adjective_name is None else self.forward_evaluation(self.framework.get_adjective(self.condition.obj1_pointer_adjective_name), node)
            obj2 = self.forward_evaluation(self.framework.get_adjective(self.condition.obj2_pointer_adjective_name), node)
            comparison_adjective = self.framework.get_adjective(self.condition.comparison_adjective_name)
            return comparison_adjective.evaluate(obj1, obj2)

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation for the condition.
        
        :param node: The node to explain
        :type node: Any
        :return: A LogicalExpression representing the explanation
        :rtype: LogicalExpression
        """
        return self.forward_explanation(self.condition, node, no_increment=True)

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