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
    
    def __init__(self, *args, explain_further=True, forward_pointers_explanations=True): #(pointer_adjective_name: str = None, adjective_name: str = None):
        super().__init__()
        """
        Initialize the Possession explanation.

        Usage:
            Possession(adjective_name)
            Possession(pointer_adjective_name, adjective_name)
        
        Args:
            *args: Either one or two string arguments.
                   If one argument: adjective_name
                   If two arguments: pointer_adjective_name, adjective_name

            pointer_adjective_name: The name of the pointer adjective that selects the object.
                                    If not given the node itself will be checked.
            adjective_name: The name of the adjective to explain for the selected object.

        Keyword argument:
            explain_further (bool): Wether to explain the Possession or just give the consequent without antecedent.
            forward_pointers_explanations (bool): whether it is necessary to explain why the node has the given pointer adjectives attached.
        """
        
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
        self.forward_pointers_explanations = forward_pointers_explanations

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation by explaining the underlying possession adjectives.
        Only Assumptions don't redirect to other explanations.
        
        Args:
            node: The node containing the pointer adjective.
            
        
        Returns:
            A LogicalExpression representing the explanation of the specified adjective for the selected object.
        """        
        adjective = self.framework.get_adjective(self.adjective_name)

        if not self.pointer_adjective_name: # the possession refers to the self node
            explanation = self.forward_explanation(adjective, node, explain_further=self.explain_further) # Why the node has this property?

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
            referred_object = self.forward_evaluation(pointer_adjective, node)

            if not self.forward_pointers_explanations:
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

    def __init__(self, *args, explain_further = True, forward_pointers_explanations = True): #(obj1_pointer_adjective_name: str, comparison_adjective_name: str, obj2_pointer_adjective_name: str)
        super().__init__()
        """
        Initialize the Comparison explanation.

        Usage:
            Comparison(comparison_adjective_name, obj2_pointer_adjective_name)
            Comparison(obj1_pointer_adjective_name, comparison_adjective_name, obj2_pointer_adjective_name)

            The first case takes the current node as first object of comparison
        
        Args:
            *args: Either two or three string arguments.
                   If two argument: comparison_adjective_name, obj2_pointer_adjective_name
                   If three arguments: obj1_pointer_adjective_name, comparison_adjective_name, obj2_pointer_adjective_name)

            obj1_pointer_adjective_name: The name of the pointer adjective that selects the first object to compare.
                                        If not given the node itself will be used.
            comparison_adjective_name: The name of the adjective to use for the comparison.
            obj2_pointer_adjective_name : The name of the pointer adjective that selects the second object to compare.7

        Keyword argument:
            explain_further (bool): Wether to explain the Possession or just give the consequent without antecedent.
            forward_pointers_explanations (bool): whether it is necessary to explain why the objects have the given adjectives attached.
        """
        
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
        self.forward_pointers_explanations = forward_pointers_explanations

    def _explain(self, node: Any):

        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)
        
        obj2_pointer_adjective = self.framework.get_adjective(self.obj2_pointer_adjective_name)
        obj2 = self.forward_evaluation(obj2_pointer_adjective, node)

        if self.obj1_pointer_adjective_name is None:
            if self.forward_pointers_explanations:
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

            if self.forward_pointers_explanations:
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
        super().__init__()
        """
        Initialize the ComparisonNodesPropertyPossession Explanation.
        
        Args:
            adjective_for_comparison_name: The adjective name of the property to compare.
        """
        self.adjective_for_comparison_name = adjective_for_comparison_name

    def _explain(self, node: Any) -> Proposition:
        """
        Generate an explanation for the possession of a property on a node and another node to be compared to.
        
        Args:
            node: The main node to explain.
            other_nodes: The nodes that it is compared to.
            
        
        Returns:
            A Proposition explaining the possession of the property values for both nodes.
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
        super().__init__()
        """
        Initialize the Group Comparison explanation.
        
        Args:
            comparison_adjective_name: The name of the comparison adjective.
            group_pointer_adjective_name: a callable that given a node returns an array of objects to compare
            positive_implication: If the implication in the framework is seeking for a positive implication of
                                inference of the comparison adjective or a negative implication:
                                e.g. better than OR not(better than)?
        """
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name
        self.positive_implication = positive_implication

    def _explain(self, node: Any) -> Proposition:
        """
        Generate an explanation for the comparison between a node and all nodes pointed at
        by the group pointer adjective specified.
        
        Args:
            node: The node to explain.            
        
        Returns:
            A Proposition explaining the comparison.
        """

        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)

        group_pointer_adjective = self.framework.get_adjective(self.group_pointer_adjective_name)
        group = self.forward_evaluation(group_pointer_adjective, node)

        group_explanation = self.forward_explanation(group_pointer_adjective, node)
        comparison_explanations = self.forward_explanation(comparison_adjective, node, group)
        
        comparison_explanations.consequent.expr = f"{self.comparison_adjective_name} them" # Remove redundant information
        explanation = And(group_explanation, comparison_explanations)
        return explanation
