from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterable

from src.explainer.propositional_logic import Proposition, And, Or, Implies, Not
from src.explainer.condition import Condition

class Explanation(ABC):
    """Abstract base class for all types of explanations."""
    
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

class AssumptionExplanation(Explanation):
    """Represents an explanation based on an assumption."""
    
    def __init__(self, description: str):
        """
        Initialize the AssumptionExplanation.
        
        Args:
            description: A string describing the assumption.
        """
        self.description = description

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """Return the assumption as a Proposition."""
        return Proposition(self.description)

class AdjectiveExplanation(Explanation):
    """
    Represents an explanation for an object referred to by
    a pointer adjective to possess a given static adjective.
    """
    
    def __init__(self, pointer_adjective_name: str, adjective_name: str):
        """
        Initialize the AdjectiveExplanation.
        
        Args:
            pointer_adjective_name: The name of the pointer adjective that selects the object.
            adjective_name: The name of the adjective to explain for the selected object.
        """
        self.pointer_adjective_name = pointer_adjective_name
        self.adjective_name = adjective_name

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate an explanation by redirecting to explain_adjective for the selected object.
        
        Args:
            node: The node containing the pointer adjective.
            context: Additional context, including the explainer.
        
        Returns:
            A Proposition representing the explanation of the specified adjective for the selected object.
        """
        explainer = context['explainer']
        pointer_adjective = explainer.framework.get_adjective(self.pointer_adjective_name)
        referred_object = pointer_adjective.evaluate(node)
        return explainer.explain_adjective(referred_object, self.adjective_name) # recursion


class ConditionalExplanation(Explanation):
    """Represents an explanation that depends on a condition."""
    
    def __init__(self, condition: Condition, true_explanation: Explanation, false_explanation: Explanation):
        """
        Initialize the ConditionalExplanation.
        
        Args:
            condition: The condition to evaluate.
            true_explanation: The explanation to use when the condition is true.
            false_explanation: The explanation to use when the condition is false.
        """
        self.condition = condition
        self.true_explanation = true_explanation
        self.false_explanation = false_explanation

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate an explanation based on the condition's evaluation.
        
        Args:
            node: The node to explain.
            context: Additional context for the explanation.
        
        Returns:
            A Proposition representing the condition and the appropriate explanation.
        """
        condition_result = self.condition.evaluate(node, context)

        if self.condition.value == True or self.condition.value == False: # if the value is a boolean
            if self.condition.value:
                end_sentence = f"is {self.condition.adjective_name}"
            else:
                end_sentence = f"is not {self.condition.adjective_name}"
        else:
            end_sentence = f"has {self.condition.adjective_name} = {self.condition.value})"

        if not self.condition.pointer_adjective_name: 
            condition_explanation = Proposition(f"The node {end_sentence}")
        else:
            condition_explanation = Proposition(f"The {self.condition.pointer_adjective_name} {end_sentence}")

        if condition_result:
            return And(condition_explanation, self.true_explanation.explain(node, context))
        else:
            return And(Not(condition_explanation), self.false_explanation.explain(node, context))

class CompositeExplanation(Explanation):
    """Represents an explanation composed of multiple sub-explanations."""
    
    def __init__(self, *explanations: Explanation):
        """
        Initialize the CompositeExplanation.
        
        Args:
            *explanations: Variable number of Explanation objects to be combined.
        """
        self.explanations = explanations

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate an explanation by combining all sub-explanations with AND.
        
        Args:
            node: The node to explain.
            context: Additional context for the explanation.
        
        Returns:
            A Proposition representing the combination of all sub-explanations.
        """
        return And(*[exp.explain(node, context) for exp in self.explanations])

""" Double argument Explanations """
class ComparisonAssumptionExplanation(Explanation):
    """Represents an assumption based on a comparison between two nodes."""
    
    def __init__(self, ranking_adjective_name: str, pointer_adjective_name: str, operator: str):
        """
        Initialize the ComparisonAssumptionExplanation.
        
        Args:
            ranking_adjective_name: The name of the ranking adjective.
            pointer_adjective_name: The name of the pointer adjective used for comparison.
            comparison_operator: The comparison function.
        """
        self.ranking_adjective_name = ranking_adjective_name
        self.pointer_adjective_name = pointer_adjective_name
        self.operator = operator

    def explain(self, node1: Any, node2: Any, context: Dict[str, Any], negation=False) -> Proposition:
        """
        Generate an explanation for the comparison between two nodes.
        
        Args:
            node1: The first node to compare.
            node2: The second node to compare.
            context: Additional context for the explanation.
        
        Returns:
            A Proposition explaining the comparison.
        """
        proposition = Proposition(f"{node1}.{self.pointer_adjective_name} {self.operator} {node2}.{self.pointer_adjective_name}")
        if not negation:
            return proposition
        else:
            return Not(proposition)

class ComparisonExplanation(Explanation):
    """Represents an explanation for a comparison between a node 
    and an other node referenced via pointer adjective."""
    
    def __init__(self, ranking_adjective_name: str, pointer_adjective_name: str):
        """
        Initialize the ComparisonExplanation.
        
        Args:
            ranking_adjective_name: The name of the ranking adjective.
            pointer_adjective_name: The name of the pointer adjective that selects the object.
        """
        self.ranking_adjective_name = ranking_adjective_name
        self.sibling_selector = sibling_selector

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate an explanation for the comparison between a node and its adjective reference.
        
        Args:
            node: The node to explain.
            context: Additional context for the explanation.
        
        Returns:
            A Proposition explaining the comparison.
        """
        explainer = context['explainer']
        pointer_adjective = explainer.framework.get_adjective(self.pointer_adjective_name)
        referred_object = pointer_adjective.evaluate(node)
        comparison = _ObjectComparisonExplanation(self.pointer_adjective_name, referred_object)
        return comparison.explain(node, context)

class SiblingsComparisonExplanation(Explanation):
    """Represents an explanation for a comparison between a node and its sibling."""
    
    def __init__(self, ranking_adjective_name: str, siblings_selector: Callable[[Any], Iterable[Any]]):
        """
        Initialize the SiblingsComparisonExplanation.
        
        Args:
            ranking_adjective_name: The name of the ranking adjective.
            siblings_selector: The selector of sibling: a callable that given a node returns an array of siblings
        """
        self.ranking_adjective_name = ranking_adjective_name
        self.siblings_selector = siblings_selector

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate an explanation for the comparison between a node and its adjective reference.
        
        Args:
            node: The node to explain.
            context: Additional context for the explanation.
        
        Returns:
            A Proposition explaining the comparison.
        """
        siblings = self.siblings_selector(node)
        explanations = [
            _ObjectComparisonExplanation(self.ranking_adjective_name, sibling)
            for sibling in siblings]
        
        return CompositeExplanation(*explanations).explain(node, context)

class _ObjectComparisonExplanation(Explanation):
    def __init__(self, ranking_adjective_name: str, referred_object: Any):
        """
        Initialize the ComparisonExplanation.
        
        Args:
            ranking_adjective_name: The name of the ranking adjective.
            referred_object: The object to compare
        """
        self.ranking_adjective_name = ranking_adjective_name
        self.referred_object = referred_object

    def explain(self, node: Any, context: Dict[str, Any]) -> Proposition:
        """
        Generate an explanation for the comparison between a node and an object.
        
        Args:
            node: The node to explain.
            context: Additional context for the explanation.
        
        Returns:
            A Proposition explaining the comparison.
        """
        explainer = context['explainer']
        return explainer.explain_adjective(node, self.ranking_adjective_name, self.referred_object)
