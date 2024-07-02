from abc import ABC, abstractmethod
from typing import Any, Callable

from src.explainer.propositional_logic import LogicalExpression, Proposition, And, Or, Implies, Not
from src.explainer.framework import ArgumentationFramework

"""
Explanations are the base of inference for an adjective to be assigned.
Why is a node leaf?
Why is a node's score = 4?
Why is a node better than another?

All Explanations redirect to underlying explanations.
Only Assumptions don't, stopping the explanation inception.
"""

class Explanation(ABC):
    """Abstract base class for all types of explanations."""
    
    def set_belonging_framework(self, framework: ArgumentationFramework, adjective: 'Adjective'):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.framework = framework
        self.explanation_of_adjective = adjective
        self.contextualize()
    
    def contextualize(self):
        pass

    @abstractmethod
    def explain(self, node: Any) -> LogicalExpression:
        """
        Generate a propositional logic explanation for the given node.
        
        Args:
            node: The node to explain.
        
        Returns:
            A LogicalExpression representing the explanation.
        """
        pass

    @abstractmethod
    def implies(self) -> LogicalExpression:
        """
        Generate a propositional logic explanation decontextualized.
        It should reflect in an abstract way the implication of the
        explanation.
        
        Returns:
            A LogicalExpression representing the explanation.
        """
        pass

""" Assumptions """
class Assumption(Explanation):
    """Represents an explanation based on an assumption."""
    
    def __init__(self, description: str):
        """
        Initialize the Assumption.
        
        Args:
            description: A string describing the assumption.
        """
        self.description = description

    def explain(self, node: Any) -> LogicalExpression:
        """Return the assumption as a Proposition."""
        return Proposition("(assumption) " + self.description)
    
    def implies(self) -> LogicalExpression:
        """Return the assumption as a Proposition."""
        return Proposition("(assumption) " + self.description)

class BooleanAdjectiveAssumption(Assumption):
    """Represents the assumption underlying a boolean adjective attribution."""
    
    def __init__(self, adjective_name: str):
        """
        Initialize the ComparisonAssumption.
        
        Args:
            adjective_name: The name of the boolean adjective.
        """
        description = f"By definition of \"{adjective_name}\""
        super().__init__(description)

class ComparisonAssumption(Assumption):
    """Represents the assumption underlying the comparison between two nodes."""
    
    def __init__(self, comparison_adjective_name: str, pointer_adjective_name: str, operator: str):
        """
        Initialize the ComparisonAssumption.
        
        Args:
            ranking_adjective_name: The name of the ranking adjective.
            pointer_adjective_name: The name of the pointer adjective used for comparison.
            comparison_operator: The comparison function.
        """
        description = f"By definition, node1 is \"{comparison_adjective_name}\" than node2 if node1 {pointer_adjective_name} {operator} node2 {pointer_adjective_name}"
        super().__init__(description)

class RankAssumption(Assumption):
    """Represents the assumption underlying the comparison between two nodes."""
    def __init__(self, rank_type : str, name: str, comparison_adjective_name: str, group_pointer_adjective_name: str):
        """
        Initialize the ComparisonAssumption.
        
        Args:
            ranking_adjective_name: The name of the ranking adjective.
            pointer_adjective_name: The name of the pointer adjective used for comparison.
            comparison_operator: The comparison function.
        """
        if rank_type == 'max':
            description = f"By definition a node is \"{name}\" if it's \"{comparison_adjective_name}\" compared to all nodes among \"{group_pointer_adjective_name}\""
        elif rank_type == 'min':
            negate = Not('\"' + comparison_adjective_name + '\"')
            description = f"By definition a node is \"{name}\" if it's {negate} compared to all nodes among \"{group_pointer_adjective_name}\""
        else:
            raise ValueError("RankAssumption of unknown type.")
        super().__init__(description)

""" Straightforward Explanations """
class Possession(Explanation):
    """
    Represents an explanation provided by referring to the fact that
    a given pointer adjective possess a given adjective.
    """
    
    def __init__(self, *args): #pointer_adjective_name: str = None, adjective_name: str = None):
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
        """
        
        if len(args) == 1:
            # If they did not provide 2 arguments, the first is the adjective name
            self.pointer_adjective_name = None
            self.adjective_name = args[0]
        elif len(args) == 2:
            # If two arguments are provided, the first is the pointer adjective name
            self.pointer_adjective_name, self.adjective_name = args
        else:
            raise ValueError("AdjectiveExplanation takes a max of 2 arguments")

    def explain(self, node: Any) -> LogicalExpression:
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
            return adjective.explain(node)

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
            referred_object = pointer_adjective.evaluate(node)

            if self.explanation_of_adjective == pointer_adjective:
                # only forward the explanation without asking why this referred object
                explanation = adjective.explain(referred_object)
            else:
                explanation = And(
                    pointer_adjective.explain(node), # why this referred_object?
                    adjective.explain(referred_object)) # why the referred_object has this property?
            return explanation
    
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
                implication = adjective.implies()
            else:
                implication = And(
                    pointer_adjective.implies(), # why this referred_object?
                    adjective.implies(evaluation)) # why the referred_object has this property?
            return implication

class Comparison(Explanation):
    """Represents an explanation provided by referring to a comparison
    between the node and another node referenced via pointer adjective."""
    
    def __init__(self, comparison_adjective_name: str, node_pointer_adjective_name: str):
        """
        Initialize the Comparison Explanation.
        
        Args:
            comparison_adjective_name: The name of the comparison adjective.
            pointer_adjective_name: The name of the pointer adjective that selects the object.
        """
        self.comparison_adjective_name = comparison_adjective_name
        self.node_pointer_adjective_name = node_pointer_adjective_name

    def explain(self, node: Any) -> Proposition:
        """
        Generate an explanation for the comparison between a node and its adjective reference.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A Proposition explaining the comparison.
        """
        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)
        property_for_comparison_adjective = self.framework.get_adjective(comparison_adjective.property_pointer_adjective_name)

        node_pointer_adjective = self.framework.get_adjective(self.node_pointer_adjective_name)
        other_node = node_pointer_adjective.evaluate(node)

        explanation = And(
            property_for_comparison_adjective.explain(node),
            property_for_comparison_adjective.explain(other_node), 
            comparison_adjective.explain(node, other_node))

        return explanation

    def implies(self) -> LogicalExpression:
        return Proposition(f"node1 is {self.comparison_adjective_name} than node2")


""" Group Comparison non-straightforward Explanation """
class GroupComparison(Explanation):
    """Represents an explanation given by referring to 
    a comparison between a node and all nodes of a group."""
    
    def __init__(self, comparison_adjective_name: str, group_pointer_adjective_name: str, positive_implication: bool = True):
        """
        Initialize the Group Comparison explanation.
        
        Args:
            comparison_adjective_name: The name of the comparison adjective.
            siblings_selector: The selector of sibling: a callable that given a node returns an array of siblings
            positive_implication: If the implication in the framework is seeking for a positive implication of
                                inference of the comparison adjective or a negative implication:
                                e.g. better than OR not(better than)?
        """
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name
        self.positive_implication = positive_implication

    def explain(self, node: Any) -> Proposition:
        """
        Generate an explanation for the comparison between a node and all nodes pointed at
        by the group pointer adjective specified.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A Proposition explaining the comparison.
        """

        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)
        value_for_comparison_adjective = self.framework.get_adjective(comparison_adjective.property_pointer_adjective_name)

        group_pointer_adjective = self.framework.get_adjective(self.group_pointer_adjective_name)
        group = group_pointer_adjective.evaluate(node)

        explanations = [And(
            value_for_comparison_adjective.explain(node),
            value_for_comparison_adjective.explain(other_node), 
            comparison_adjective.explain(node, other_node))
            for other_node in group]
        explanation = And(*explanations)
        return explanation

    def implies(self, evaluation = True) -> LogicalExpression:
        return Proposition(f"Node {self.comparison_adjective_name if self.positive_implication else Not(self.comparison_adjective_name)} than all nodes in {self.group_pointer_adjective_name}")

""" Composite Explanations """
class CompositeExplanation(Explanation):
    """Represents an explanation composed of multiple sub-explanations."""
    
    def __init__(self, *explanations: Explanation):
        """
        Initialize the CompositeExplanation.
        
        Args:
            *explanations: Variable number of Explanation objects to be combined.
        """
        self.explanations = explanations

    def contextualize(self):
        for exp in self.explanations:
            exp.set_belonging_framework(self.framework, self.explanation_of_adjective)

    def explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation by combining all sub-explanations with AND.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A LogicalExpression representing the combination of all sub-explanations.
        """
        return And(*[exp.explain(node) for exp in self.explanations])
    
    def implies(self) -> LogicalExpression:
        return And(*[exp.implies() for exp in self.explanations])

""" Conditional Explanations """
class PossessionCondition(Possession):
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
    
    #implies() method from Possession

    def evaluate(self, node: Any) -> bool:
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
            obj_under_evaluation = pointer_adjective.evaluate(node)

        adjective = self.framework.get_adjective(self.adjective_name)
        return adjective.evaluate(obj_under_evaluation) == self.value


class ConditionalExplanation(Explanation):
    """Represents an explanation that depends on a condition."""
    
    def __init__(self, condition: PossessionCondition, true_explanation: Explanation, false_explanation: Explanation):
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

    def contextualize(self):
        self.condition.set_belonging_framework(self.framework, self.explanation_of_adjective)
        self.true_explanation.set_belonging_framework(self.framework, self.explanation_of_adjective)
        self.false_explanation.set_belonging_framework(self.framework, self.explanation_of_adjective)

    def explain(self, node: Any) -> LogicalExpression:
        """
        Generate an explanation based on the condition's evaluation.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A LogicalExpression representing the condition and the appropriate explanation.
        """
        if not node:
            return self.imply()
        condition_result = self.condition.evaluate(node)

        if condition_result:
            explanation = And(
                        self.condition.explain(node), 
                        self.true_explanation.explain(node))
        else:
            explanation = And(
                        self.condition.explain(node), 
                        self.false_explanation.explain(node))
        return explanation

    def implies(self) -> LogicalExpression:
        explanation1 = And(
                        self.condition.implies(True), 
                        self.true_explanation.implies())
        explanation2 = And(
                        self.condition.implies(False), 
                        self.false_explanation.implies())
        return Or(explanation1, explanation2)
