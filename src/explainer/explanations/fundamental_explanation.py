from .base import Explanation
from src.explainer.common.utils import AdjectiveType

from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And

from typing import Any

""" Straightforward Explanations """
class Possession(Explanation):
    """
    Represents an explanation provided by referring to the fact that
    a given pointer adjective possess a given adjective.
    """
    
    def __init__(self, *args, explain_further=True, forward_possessions_explanations=True): #(pointer_adjective_name: str = None, adjective_name: str = None):
        """
        Initialize the Possession explanation.

        Usage:
            Possession(adjective_name)
            Possession(pointer_adjective_name, adjective_name)
        
        :param args: Either one or two string arguments.
                     If one argument: adjective_name
                     If two arguments: pointer_adjective_name, adjective_name
        :type args: str
        :param explain_further: Whether to explain the Possession or just give the consequent without antecedent, optional.
        :type explain_further: bool
        :param forward_possessions_explanations: Whether it is necessary to explain why the node has the given pointer adjectives attached, optional.
        :type forward_possessions_explanations: bool
        :raises ValueError: If more than 2 non-keyword arguments are provided.

        pointer_adjective_name: The name of the pointer adjective that selects the object.
                                If not given the node itself will be checked.
        adjective_name: The name of the adjective to explain for the selected object.
        """
        super().__init__()
        if len(args) == 1:
            # If they did not provide 2 arguments, the first is the adjective name
            self.pointer_adjective_name = None
            self.adjective_name = args[0]
        elif len(args) == 2:
            # If two arguments are provided, the first is the pointer adjective name
            self.pointer_adjective_name, self.adjective_name = args
        else:
            raise ValueError("A Possession explanation takes a max of 2 non-keyword arguments")
        
        self.explain_further = explain_further
        self.forward_possessions_explanations = forward_possessions_explanations

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation by explaining the underlying possession adjectives.
        Only Assumptions don't redirect to other explanations.
        
        :param node: The node containing the pointer adjective.
        :type node: Any
        :return: A :class:`LogicalExpression` representing the explanation of the specified adjective for the selected object.
        :rtype: LogicalExpression
        """        
        adjective = self.framework.get_adjective(self.adjective_name)

        if not self.pointer_adjective_name: # the possession refers to the self node
            explanation = self.forward_explanation(adjective, node, explain_further=self.explain_further) # Why the node has this property?

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
            referred_object = self.forward_evaluation(pointer_adjective, node)

            if not self.forward_possessions_explanations:
                explanation = self.forward_explanation(adjective, referred_object, explain_further=self.explain_further) # why the referred_object has this property?
            elif self.explanation_of_adjective == pointer_adjective:
                # only forward the explanation without asking why this referred object
                # otherwise we would get into an infinite recursion,
                # by trying to explain the pointer adjective by referring to it.
                explanation = self.forward_explanation(adjective, referred_object, explain_further=self.explain_further) # why the referred_object has this property?
            else:
                explanations = self.forward_multiple_explanations(
                    (pointer_adjective, node), # why this referred_object?
                    (adjective, referred_object), # why the referred_object has this property?
                    explain_further=self.explain_further
                )
                explanation = And(*explanations)
        
        return explanation
        
class Comparison(Explanation):
    """Represents an explanation given by referring to 
    a comparison between a node and another."""

    def __init__(self, *args, explain_further = True, forward_possessions_explanations = True): #(obj1_pointer_adjective_name: str, comparison_adjective_name: str, obj2_pointer_adjective_name: str)
        """
        Initialize the Comparison explanation.

        Usage:
            Comparison(comparison_adjective_name, obj2_pointer_adjective_name)
            Comparison(obj1_pointer_adjective_name, comparison_adjective_name, obj2_pointer_adjective_name)

            The first case takes the current node as first object of comparison
        
        :param args: Either two or three string arguments.
                     If two argument: comparison_adjective_name, obj2_pointer_adjective_name
                     If three arguments: obj1_pointer_adjective_name, comparison_adjective_name, obj2_pointer_adjective_name)
        :type args: str
        :param explain_further: Whether to explain the Possession or just give the consequent without antecedent, optional.
        :type explain_further: bool
        :param forward_possessions_explanations: Whether it is necessary to explain why the objects have the given adjectives attached, optional.
        :type forward_possessions_explanations: bool
        :raises ValueError: If less than 2 or more than 3 arguments are provided.

        obj1_pointer_adjective_name: The name of the pointer adjective that selects the first object to compare.
                                    If not given the node itself will be used.
        comparison_adjective_name: The name of the adjective to use for the comparison.
        obj2_pointer_adjective_name : The name of the pointer adjective that selects the second object to compare.7
        """
        super().__init__()
        if len(args) == 2:
            # If they did not provide 2 arguments, the first is the comparison_adjective_name
            self.obj1_pointer_adjective_name = None
            self.comparison_adjective_name = args[0]
            self.obj2_pointer_adjective_name = args[1]
        elif len(args) == 3:
            # If two arguments are provided, the first is the pointer obj1_pointer_adjective_name
            self.obj1_pointer_adjective_name, self.comparison_adjective_name, self.obj2_pointer_adjective_name = args
        else:
            raise ValueError("A Comparison explanation takes a min of 2 and a max of 3 arguments")

        self.explain_further = explain_further
        self.forward_possessions_explanations = forward_possessions_explanations

    def _explain(self, node: Any):

        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)
        
        obj2_pointer_adjective = self.framework.get_adjective(self.obj2_pointer_adjective_name)
        obj2 = self.forward_evaluation(obj2_pointer_adjective, node)

        if self.obj1_pointer_adjective_name is None:
            if self.forward_possessions_explanations:
                explanations = self.forward_multiple_explanations(
                        (comparison_adjective, node, obj2), # why obj1 is <(e.g.) better> than obj2?
                        (obj2_pointer_adjective, node), # why the node has this pointer adjective?
                        explain_further=self.explain_further
                    )
                explanation = And(*explanations)
            else:
                explanation = self.forward_explanation(comparison_adjective, node, obj2, explain_further=self.explain_further)
            
        else:
            obj1_pointer_adjective = self.framework.get_adjective(self.obj1_pointer_adjective_name)
            obj1 = self.forward_evaluation(obj1_pointer_adjective, node)

            if self.forward_possessions_explanations:
                explanations = self.forward_multiple_explanations(
                        (comparison_adjective, obj1, obj2), # why obj1 is <(e.g.) better> than obj2?
                        (obj1_pointer_adjective, node), # why the node has this pointer adjective?
                        (obj2_pointer_adjective, node), # why the node has this pointer adjective?
                        explain_further=self.explain_further
                    )
                explanation = And(*explanations)
            else:
                explanation = self.forward_explanation(comparison_adjective, obj1, obj2, explain_further=self.explain_further)

        return explanation

class ComparisonNodesPropertyPossession(Explanation):
    """Represents an explanation provided by referring to the possession
    of a specific adjective value by two nodes that are to be compared."""
    
    def __init__(self, adjective_for_comparison_name: str):
        """
        Initialize the ComparisonNodesPropertyPossession Explanation.
        
        :param adjective_for_comparison_name: The adjective name of the property to compare.
        :type adjective_for_comparison_name: str
        """
        super().__init__()
        self.adjective_for_comparison_name = adjective_for_comparison_name

    def _explain(self, node: Any) -> Proposition:
        """
        Generate an explanation for the possession of a property on a node and another node to be compared to.
        
        :param node: The main node to explain.
        :type node: Any
        :return: A :class:`Proposition` explaining the possession of the property values for both nodes.
        :rtype: Proposition
        """
        adjective_for_comparison = self.framework.get_adjective(self.adjective_for_comparison_name)
        if self.explanation_of_adjective.type == AdjectiveType.COMPARISON:
            other_nodes = self.framework.get_adjective(self.COMPARISON_AUXILIARY_ADJECTIVE).evaluate(node)
        else:
            raise ValueError("The ComparisonNodesPropertyPossession should be the explanation of a comparison adjective.")

        if type(other_nodes) is not list:
            other_nodes = [other_nodes]

        to_forward_explanations = [(adjective_for_comparison, node)]
        for o_node in other_nodes:
            to_forward_explanations.append((adjective_for_comparison, o_node))

        explanations = self.forward_multiple_explanations(*to_forward_explanations)
        
        explanation = And(*explanations)

        return explanation

""" Group Comparison non-straightforward Explanation """
class GroupComparison(Explanation):
    """Represents an explanation given by referring to 
    a comparison between a node and all nodes of a group."""
    
    def __init__(self, comparison_adjective_name: str, group_pointer_adjective_name: str, positive_implication: bool = True):
        """
        Initialize the Group Comparison explanation.
        
        :param comparison_adjective_name: The name of the comparison adjective.
        :type comparison_adjective_name: str
        :param group_pointer_adjective_name: a callable that given a node returns an array of objects to compare
        :type group_pointer_adjective_name: str
        :param positive_implication: If the implication in the framework is seeking for a positive implication of
                                    inference of the comparison adjective or a negative implication:
                                    e.g. better than OR not(better than)? Optional.
        :type positive_implication: bool
        """
        super().__init__()
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name
        self.positive_implication = positive_implication

    def _explain(self, node: Any) -> Proposition:
        """
        Generate an explanation for the comparison between a node and all nodes pointed at
        by the group pointer adjective specified.
        
        :param node: The node to explain.
        :type node: Any
        :return: A :class:`Proposition` explaining the comparison.
        :rtype: Proposition
        """

        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)

        group_pointer_adjective = self.framework.get_adjective(self.group_pointer_adjective_name)
        group = self.forward_evaluation(group_pointer_adjective, node)

        group_explanation = self.forward_explanation(group_pointer_adjective, node)
        comparison_explanations = self.forward_explanation(comparison_adjective, node, group)
        
        comparison_explanations.consequent.object = "them" # Remove redundant information
        explanation = And(group_explanation, comparison_explanations)
        return explanation

class RecursivePossession(Explanation):
    """
    Represents an explanation provided by referring to the fact that
    the object referred to by a given pointer adjective possess a given pointer adjective,
    and this same pointer adjective refers to an object, which will possess the same given adjective,
    recursively continuing until a condition is met.

    e.g. RecursivePossession("next move", any_stop_conditions = [If("final move"), If("fully searched")])
    """
    max_recursion_depth = 5
    
    def __init__(self, *args, any_stop_conditions: list['If'], explain_further=False, forward_possessions_explanations=True): #(pointer_adjective_name: str = None, adjective_name: str = None):
        """
        Initialize the RecursivePossession explanation.

        Usage:
            RecursivePossession(pointer_adjective_name, any_stop_conditions=[If(adjective)])
            RecursivePossession(start_pointer_adjective_name, pointer_adjective_name, any_stop_conditions=[If(adjective)])
        
        :param args: Either one or two string arguments.
                     If one argument: pointer_adjective_name
                     If two arguments: start_pointer_adjective_name, pointer_adjective_name
        :type args: str
        :param any_stop_conditions: The conditions to stop the recursion. Any of them will stop it.
        :type any_stop_conditions: list['If']
        :param explain_further: Whether to explain the Possession or just give the consequent without antecedent, optional.
        :type explain_further: bool
        :param forward_possessions_explanations: Whether it is necessary to explain why the node has the given pointer adjectives attached, optional.
        :type forward_possessions_explanations: bool
        :raises ValueError: If more than 2 non-keyword arguments are provided.

        start_pointer_adjective_name: The name of the pointer adjective that selects the object from which to start.
                                    If not given, the node itself will be checked.
        pointer_adjective_name: The name of the adjective to explain for the selected object.
        """
        super().__init__()
        if len(args) == 1:
            # If they did not provide 2 arguments, the first is the adjective name
            self.start_pointer_adjective_name = None
            self.pointer_adjective_name = args[0]
        elif len(args) == 2:
            # If two arguments are provided, the first is the pointer adjective name
            self.start_pointer_adjective_name, self.pointer_adjective_name = args
        else:
            raise ValueError("A RecursivePossession explanation takes a max of 2 non-keyword arguments")
        
        self.any_stop_conditions = any_stop_conditions
        self.explain_further = explain_further
        self.forward_possessions_explanations = forward_possessions_explanations

        for condition in any_stop_conditions:
            condition.forward_possessions_explanations = False

    def _explain(self, node: Any, *, recursion_explanations=None, recursion_depth=0) -> LogicalExpression:
        """
        Generate an explanation by explaining the underlying possession adjectives.
        Only Assumptions don't redirect to other explanations.
        
        Args:
            node: The node containing the pointer adjective.
            
        
        Returns:
            A LogicalExpression representing the explanation of the specified adjective for the selected object.
        """
        if recursion_explanations is None:
            recursion_explanations = []
        
        # Take the next object to continue the recursion with:
        pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
        next_object_in_recursion = self.forward_evaluation(pointer_adjective, node)

        if not self.start_pointer_adjective_name: # the possession refers to the self node
            explanation = self.forward_multiple_explanations((pointer_adjective, node), explain_further=self.explain_further) # Why the node has this property?

        else:
            start_pointer_adjective = self.framework.get_adjective(self.start_pointer_adjective_name)
            start_object = self.forward_evaluation(start_pointer_adjective, node)

            if not self.forward_possessions_explanations:
                explanation = self.forward_multiple_explanations((pointer_adjective, start_object), explain_further=self.explain_further) # why the start_object has this pointer_adjective?
            elif self.explanation_of_adjective == start_pointer_adjective:
                # only forward the explanation without asking why this referred object
                # otherwise we would get into an infinite recursion,
                # by trying to explain the pointer adjective by referring to it.
                explanation = self.forward_multiple_explanations((pointer_adjective, start_object), explain_further=self.explain_further) # why the referred_object has this property?
            else:
                explanation = self.forward_multiple_explanations(
                    (start_pointer_adjective, node), # why this referred_object?
                    (pointer_adjective, start_object), # why the referred_object has this property?
                    explain_further=self.explain_further
                )
        
        if recursion_depth > 0:
            for e in explanation:
                # TODO: Move this modification as a last explanation tactic to apply because
                # the subjects of the propositions might be important for other explanation tactics.
                e.subject = "this"
        recursion_explanations.extend(explanation)

        true_stop_conditions = [
            stop_condition for stop_condition in self.any_stop_conditions
            if self.forward_evaluation(stop_condition, node)
        ]
        any_stop_condition_true = bool(true_stop_conditions)

        if recursion_depth > self.max_recursion_depth or any_stop_condition_true:
            # Add the condition explanation
            additional_conditions_explanations = []
            to_forward_explanations = []
            if any_stop_condition_true:
                for stop_condition in true_stop_conditions:
                    to_forward_explanations.append((stop_condition, node))

                additional_conditions_explanations = self.forward_multiple_explanations(
                    *to_forward_explanations, 
                    no_increment = True,
                    explain_further = True # The stop condition is explained further regardless
                )
            if recursion_depth > self.max_recursion_depth:
                additional_conditions_explanations.append(Postulate("Max recursion limit hitted in Recursive Possession explanation."))
                
            recursion_explanations.extend(additional_conditions_explanations)
            explanation = And(*recursion_explanations)
            return explanation
        else:
            return self._explain(next_object_in_recursion, recursion_explanations=recursion_explanations, recursion_depth=recursion_depth+1)
    
    def _contextualize(self):
        for condition in self.any_stop_conditions:
            condition.contextualize(self.explanation_of_adjective)
    
    def _decontextualize(self):
        for condition in self.any_stop_conditions:
            condition.decontextualize()