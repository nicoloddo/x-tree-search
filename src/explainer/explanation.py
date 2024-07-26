from abc import ABC, abstractmethod
from typing import Any, Callable

from src.explainer.propositional_logic import LogicalExpression, Proposition, And, Or, Not
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
    def __init__(self):
        self.explanation_tactics = {}
    
    def set_belonging_framework(self, framework: ArgumentationFramework, adjective: 'Adjective'):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.framework = framework
        self.explanation_of_adjective = adjective
        self.contextualize()
    
    def contextualize(self):
        pass

    def add_explanation_tactic(self, tactic):
        self.explanation_tactics[tactic.name] = tactic

    def del_explanation_tactic(self, tactic_name):
        del self.explanation_tactics[tactic_name]

    def explain(self, node: Any, other_node: Any = None, *, current_explanation_depth) -> LogicalExpression:
        """
        Generate a propositional logic explanation for the given node.
        
        Args:
            node: The node to explain.
            other_node: Other node in case of double node explanations (e.g. comparisons)
            explanation_depth: The amount of explanations that were given
                                during the current explanation cycle
        
        Returns:
            A LogicalExpression representing the explanation.
        """

        self.current_explanation_depth = current_explanation_depth

        if current_explanation_depth > self.framework.settings.explanation_depth:
            return
        
        if other_node:
            explanation = self._explain(node, other_node)
        else:
            explanation = self._explain(node)
        
        if explanation is not None:
            # We assign to this explanation the current explanation depth.
            explanation.current_explanation_depth = current_explanation_depth
            return explanation
        else:
            return

    def forward_explanation(self, obj, *args, no_increment = False):
        increment = 0 if no_increment else 1
        #if isinstance(obj, Adjective):
            #return adjective.explain(*args, current_explanation_depth = self.current_explanation_depth + increment)
        return obj.explain(*args, current_explanation_depth = self.current_explanation_depth + increment)
    
    def forward_multiple_explanations(self, *forward_explanations, no_increment=False):
        """
        Handle multiple forward explanations with variable arguments and return an array of explanations.
        Make sure to use this forwarding method since it will keep the current_explanation depth
        consistent among the multiple explanations.

        Args:
        *forward_explanations: Variable number of tuples. Each tuple should contain:
                    (obj, *args) with
                    obj: is the Adjective or Explanation object from which to forward the explanation,
                    *args: are the arguments to pass to object.explain.
        no_increment: Boolean, if True, doesn't increment the explanation depth.

        Returns:
        list: An array of explanations returned by each obj.explain call.
        """        
        increment = 0 if no_increment else 1
        forward_explanation_depth = self.current_explanation_depth + increment
        
        explanations = []
        for obj, *args in forward_explanations:            
            explanation = obj.explain(*args, current_explanation_depth=forward_explanation_depth)
            explanations.append(explanation)
        
        return explanations

    @abstractmethod
    def _explain(self, node: Any) -> LogicalExpression:
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
    
    def __init__(self, description: str, definition: str = None):
        super().__init__()
        """
        Initialize the Assumption.
        
        Args:
            description: A string describing the assumption.
        """
        assumption = "(assumption) " + description
        
        if not definition:
            self.verbose_string = assumption
        else:
            self.verbose_string = f"{assumption} is \"{definition}\""

        self.minimal_string = Proposition("(from assumptions)")
    
    @property
    def verbose(self):
        return Proposition(self.verbose_string)
    
    @property
    def minimal(self):
        return Proposition(self.minimal_string)

    def _explain(self, node: Any) -> LogicalExpression:
        """Return the assumption as a Proposition."""
        if self.framework.settings.assumptions_verbosity == 'verbose':
            return self.verbose

        elif self.framework.settings.assumptions_verbosity == 'minimal':
            return self.minimal

        elif self.framework.settings.assumptions_verbosity == 'no':
            return None
        else:
            raise ValueError("Framework has unvalid assumptions verbosity.")
    
    def implies(self) -> LogicalExpression:
        """Return the assumption as a Proposition."""
        return self.verbose

class PossessionAssumption(Assumption):
    """Represents the assumption underlying a boolean adjective attribution."""
    
    def __init__(self, adjective_name: str, definition: str):
        """
        Initialize the ComparisonAssumption.
        
        Args:
            adjective_name: The name of the boolean adjective.
        """
        description = f"Definition of \"{adjective_name}\""
        super().__init__(description, definition)

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
            rank_type: The type of ranking (supported: max, min)
            comparison_adjective_name: The name of the comparison adjective.
            group_pointer_adjective_name: The name of the group pointer adjective among which we are ranking the node.
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
    
    def __init__(self, *args): #(pointer_adjective_name: str = None, adjective_name: str = None):
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
            explanation = self.forward_explanation(adjective, node)

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
            referred_object = pointer_adjective.evaluate(node)

            if self.explanation_of_adjective == pointer_adjective:
                # only forward the explanation without asking why this referred object
                # otherwise we would get into an infinite recursion,
                # by trying to explain the pointer adjective by referring to it.
                explanation = self.forward_explanation(adjective, referred_object) # why the referred_object has this property?
            else:
                explanations = self.forward_multiple_explanations(
                    (pointer_adjective, node), # why this referred_object?
                    (adjective, referred_object) # why the referred_object has this property?
                )
                explanation = And(*explanations)
        
        return explanation
    
    def implies(self) -> LogicalExpression:
        """ Generates a proposition that contitutes the antecedent of an
        implication explaining why a certain adjective is attributed to
        a node. """

        adjective = self.framework.get_adjective(self.adjective_name)

        if not self.pointer_adjective_name: # the possession refers to the self node
            return adjective.implies()

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)

            if self.explanation_of_adjective == pointer_adjective:
                # only forward the explanation without asking why this referred object
                implication = adjective.implies() # why the referred_object has this property?
            else:
                implication = And(
                    pointer_adjective.implies(), # why this referred_object?
                    adjective.implies()) # why the referred_object has this property?
            return implication

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

    def _explain(self, node: Any, other_node: Any) -> Proposition:
        """
        Generate an explanation for the possession of a property on a node and another node to be compared to.
        
        Args:
            node: The main node to explain.
            other_node: The node that is compared to.
            
        
        Returns:
            A Proposition explaining the possession of the property values for both nodes.
        """
        adjective_for_comparison = self.framework.get_adjective(self.adjective_for_comparison_name)

        explanations = self.forward_multiple_explanations(
                    (adjective_for_comparison, node),
                    (adjective_for_comparison, other_node)
                )
        
        explanation = And(*explanations)

        return explanation

    def implies(self) -> LogicalExpression:
        return self.framework.get_adjective(self.adjective_for_comparison_name).implies()


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
            siblings_selector: The selector of sibling: a callable that given a node returns an array of siblings
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
        group = group_pointer_adjective.evaluate(node)

        # Apply tactics
        if "OnlyRelevantComparisons" in self.explanation_tactics:
            value_for_comparison_adjective = self.framework.get_adjective(comparison_adjective.property_pointer_adjective_name)
            group = self.explanation_tactics["OnlyRelevantComparisons"].apply(group, value_for_comparison_adjective)

        to_forward_explanations = [(comparison_adjective, node, other_node) for other_node in group]
        to_forward_explanations.append((group_pointer_adjective, node))
        explanations = self.forward_multiple_explanations(*to_forward_explanations)
        base_explanation = explanations.pop() # pop the group_pointer_adjective explanation
                
        explanation = And(base_explanation, And(*explanations))
        return explanation

    def implies(self) -> LogicalExpression:
        return Proposition(f"Node {self.comparison_adjective_name if self.positive_implication else Not(self.comparison_adjective_name)} than all nodes in {self.group_pointer_adjective_name}")

""" Composite Explanations """
class CompositeExplanation(Explanation):
    """Represents an explanation composed of multiple sub-explanations."""
    
    def __init__(self, *explanations: Explanation):
        super().__init__()
        """
        Initialize the CompositeExplanation.
        
        Args:
            *explanations: Variable number of Explanation objects to be combined.
        """
        self.explanations = explanations

    def contextualize(self):
        for exp in self.explanations:
            exp.set_belonging_framework(self.framework, self.explanation_of_adjective)

    def _explain(self, node: Any, other_node: Any = None) -> LogicalExpression:
        """
        Generate an explanation by combining all sub-explanations with AND.
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A LogicalExpression representing the combination of all sub-explanations.
        """
        to_forward_explanations = []
        for exp in self.explanations:
            if exp is not None:
                if isinstance(exp, ComparisonNodesPropertyPossession):
                    to_forward_explanations.append((exp, node, other_node))
                else:
                    to_forward_explanations.append((exp, node))
        explanations = self.forward_multiple_explanations(*to_forward_explanations, no_increment = True)
        return And(*explanations)
    
    def implies(self) -> LogicalExpression:
        return And(*[exp.implies() for exp in self.explanations if exp is not None])

""" Conditional Explanations """
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

    def contextualize(self):
        self.condition.set_belonging_framework(self.framework, self.explanation_of_adjective)
        self.explanation_if_true.set_belonging_framework(self.framework, self.explanation_of_adjective)
        self.explanation_if_false.set_belonging_framework(self.framework, self.explanation_of_adjective)

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
        condition_result = self.condition.evaluate(node)

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
