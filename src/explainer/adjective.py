from abc import ABC, abstractmethod
from typing import Any, Callable
    
from src.explainer.propositional_logic import Proposition, Not, Implies
from src.explainer.explanation import *
from src.explainer.framework import ArgumentationFramework
from src.common.validators import validate_getter, validate_comparison_operator

"""
Adjectives constitute predicates by getting attributed to a node.
Only nodes can have adjectives.
A predicate in the Framework looks like:
node is <adjective> (BooleanAdjective)
node has <adjective> = value (PointerAdjective)
node <adjective> than node2 (RankingAdjective)
"""

DEFAULT_GETTER = "node.no_getter_provided"

class FrameworkAssumption:
    pass

class AdjectiveType:
    """Enum for different types of adjectives."""
    STATIC = 1  # Represents boolean attributes of nodes
    POINTER = 2  # Represents attributes that point to specific values or nodes
    COMPARISON = 3  # Represents boolean comparison between attributes of nodes

class Adjective(ABC):
    """Abstract base class for all types of adjectives."""
    
    def __init__(self, name: str, adjective_type: AdjectiveType, explanation: Explanation, *, definition: str):
        """
        Initialize the Adjective.
        
        Args:
            name: The name of the adjective.
            adjective_type: The type of the adjective (STATIC, POINTER, or RANKING).
            explanation: A callable that takes a node and context and returns a Proposition.
        Properties:
            framework: The Argumentation framework the Adjective belongs to.
            getter: The getter function for the Adjective to be evaluated with an existing node.
        """
        self.name = name
        self.type = adjective_type
        self.explanation = explanation
        self.framework = None
        self.definition = definition
        self.getter = None
        self.contextualize(definition)

    def _set_getter(self, getter: Callable[[Any], Any]):
        self.getter = getter

    def contextualize(self, getter: str):
        """ 
        Contextualizes the adjective onto the current tree by specifying
        the getter function that permits to evaluate the adjective.
        """
        validate_getter(getter)
        self._set_getter(eval(f"lambda node: {getter}"))

    def set_belonging_framework(self, framework: ArgumentationFramework):
        """Sets the Argumentation framework the Adjective belongs to."""
        self.framework = framework
        self.explanation.set_belonging_framework(framework, self)

    def evaluate(self, *args, **kwargs) -> Any:
        """
        Evaluate the adjective.
        If args are passed, evaluate in context.
        If not, this is just an implication inside abstract knowledge.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            The value of the adjective for the given node.
        """
        if len(kwargs) > 0:
            raise SyntaxError("Keyword arguments are not allowed in Adjective.evaluate().")
        if not args[0]: # We are evaluating not in context
            return None
        else:
            return self._evaluate(*args, *kwargs)

    @abstractmethod
    def _evaluate(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def proposition(self, *args, **kwargs) -> Proposition:
        """
        Create a Proposition object representing this adjective.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            A Proposition object representing this adjective.

        When defining the proposition, consider that it has to take as input
        the return of the evaluate() method to produce a consequent proposition
        in the explain() method.
        """
        pass

    def implies(self, evaluation = None) -> Implies:
        """ Returns an implication that leads from the explanation to 
        the adjective. This is like an explanation but not contextualized
        onto a specific node. """
        antecedent = self.explanation.implies()

        if self.type == AdjectiveType.COMPARISON:
            consequent = self.proposition(evaluation, [None, None])
        else:
            consequent = self.proposition(evaluation, None)

        return Implies(antecedent, consequent)

    def explain(self, node: Any, other_node: Any = None, *, current_explanation_depth) -> Implies:
        """
        Provide an explanation for the adjective's value on a given node.
        
        Args:
            node: The node to explain the adjective for.
            other_node: The optional other node for Comparison Adjectives
        
        Returns:
            An Implies object representing the explanation.
        """
        # Get propositions
        if self.type == AdjectiveType.COMPARISON:
            consequent = self.proposition(self.evaluate(node, other_node), [node, other_node])
            antecedent = self.explanation.explain(node, other_node, current_explanation_depth=current_explanation_depth)
            explanation_depth = self.explanation.current_explanation_depth
        else:
            consequent = self.proposition(self.evaluate(node), node)
            antecedent = self.explanation.explain(node, current_explanation_depth=current_explanation_depth)
            explanation_depth = self.explanation.current_explanation_depth
        
        if antecedent is not None: # If the explanation was given
            implication = Implies(antecedent, consequent)

            implication._str_settings(explanation_depth = explanation_depth)
            if self.framework.settings.print_depth:
                implication._str_settings(print_depth = self.framework.settings.print_depth)

            return implication
        else:
            return consequent

class BooleanAdjective(Adjective):
    """Represents a boolean adjective."""
    
    def __init__(self, name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None):
        """
        Initialize the BooleanAdjective.
        
        Args:
            name: The name of the adjective.
            definition: The correspondant node attribute (use the keyword "node" to refer to one of its elements).
            explanation: An explanation for the adjective.
        """
        explanation = explanation or PossessionAssumption(name, definition)
        super().__init__(name, AdjectiveType.STATIC, explanation, definition = definition)

    def proposition(self, evaluation: bool = True, node: Any = "node") -> Proposition:
        """ Returns a proposition reflecting the adjective """
        proposition = Proposition(f"{node or 'node'} is {self.name}")
        if evaluation == False:
            return Not(proposition)
        else:
            return proposition

    def _evaluate(self, node: Any) -> bool:
        """Evaluate the boolean adjective for a given node."""
        if not isinstance(self.getter(node), bool):
            raise ValueError("Boolean adjectives should evaluate as a bool.")
        return self.getter(node)

class PointerAdjective(Adjective):
    """Represents a pointer adjective that references a specific attribute or object."""
    
    def __init__(self, name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None):
        """
        Initialize the PointerAdjective.
        
        Args:
            name: The name of the adjective.
            definition: The correspondant node attribute (use the keyword "node" to refer to one of its elements).
            explanation: An explanation for the adjective.
        """
        explanation = explanation or PossessionAssumption(name, definition)
        super().__init__(name, AdjectiveType.POINTER, explanation, definition = definition)

    def proposition(self, value: Any = None, node: Any = "node") -> Proposition:
        """ Returns a proposition reflecting the pointer value """
        if not value:
            value = '?'

        proposition = Proposition(f"{node or 'node'} has {self.name} = {value or '?'}")
        return proposition

    def _evaluate(self, node: Any) -> Any:
        """Evaluate the pointer adjective for a given node."""
        return self.getter(node)

class NodesGroupPointerAdjective(PointerAdjective):
    """Represents a pointer adjective that references a group of objects. 
    You can specify an object to not include from the group definition through the "excluding" parameter.
    Example:
        NodesGroupPointerAdjective("siblings", definition = "node.parent.children", excluding = "node")
    """
    def __init__(self, name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None, *, excluding: str):
        explanation = explanation or PossessionAssumption(name, definition + " excluding " + excluding)
        if excluding:
            composite_definition = f"[element for element in {definition} if element is not {excluding}]"
        else:
            composite_definition = f"[{definition}]"
        super().__init__(name, composite_definition, explanation)
    
    def proposition(self, value: Any = None, node: Any = "node") -> Proposition:
        if not value:
            value = '?'
        elif type(value) is list:
            value = ', '.join([str(val) for val in value])
        else:
            raise ValueError(f"{self.name} NodesGroupPointerAdjective should evaluate to a list. Check your definition.")

        """ Returns a proposition reflecting the pointer value """
        proposition = Proposition(f"{node or 'node'} has {self.name} = {value or '?'}")
        return proposition

class ComparisonAdjective(Adjective):
    """Represents a ranking adjective used for comparing nodes.
    Comparison nodes do not need a getter to be evaluated."""
    
    def __init__(self, name: str, property_pointer_adjective_name: str, operator: str):
        """
        Initialize the RankingAdjective.
        
        Args:
            name: The name of the adjective.
            property_pointer_adjective_name: The name of the pointer adjective to use for comparison.
            comparison_operator: A function that compares two values and returns a boolean.
        """
        explanation = CompositeExplanation(
            ComparisonAssumption(name, property_pointer_adjective_name, operator),
            ComparisonNodesPropertyPossession(property_pointer_adjective_name))
        super().__init__(name, AdjectiveType.COMPARISON, explanation, definition=DEFAULT_GETTER)
        self.property_pointer_adjective_name = property_pointer_adjective_name

        # Validate the operator to ensure it's safe and expected
        validate_comparison_operator(operator)
        # Construct and return the lambda function
        self.comparison_operator = eval(f"lambda x, y: x {operator} y")
            

        self.operator = operator

    def proposition(self, evaluation: bool = True, node: Any = ["node1", "node2"]) -> Proposition:
        """ Returns a proposition reflecting the comparison """
        proposition = Proposition(f"{node[0] or 'node1'} is {self.name} than {node[1] or 'node1'}")
        if evaluation == False:
            return Not(proposition)
        else:
            return proposition

    def _evaluate(self, node1: Any, node2: Any) -> bool:
        """
        Evaluate the comparison between two nodes.
        
        Args:
            node1: The first node to compare.
            node2: The second node to compare.
        
        Returns:
            A boolean indicating how node1 compares to node2 with the given operator.
        """
        value1 = getattr(node1, self.property_pointer_adjective_name)
        value2 = getattr(node2, self.property_pointer_adjective_name)
        return self.comparison_operator(value1, value2)

class _RankAdjective(BooleanAdjective):
    """Represents a static (boolean) adjective that specifically refers to the
    property of being x ranked in a group, based on a given comparison adjective
    and the evaluator function. This is parent class of MaxRankAdjective and MinRankAdjective."""
    
    def __init__(self, name: str, comparison_adjective_name: str, group_pointer_adjective_name: str, explanation: Explanation, evaluator: Callable[[Any, ComparisonAdjective, PointerAdjective], bool]):
        """
        Initialize the MaxRankAdjective.
        
        Args:
            name: The name of the adjective.
            comparison_adjective:
            group_pointer_adjective:
        """
        explanation = explanation or BooleanAdjectiveAssumption(name)
        super().__init__(name, explanation=explanation)
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name
        self.evaluator = evaluator

    def _evaluate(self, node: Any) -> bool:
        """Evaluate the static adjective for a given node."""
        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)

        group = self.framework.get_adjective(self.group_pointer_adjective_name).evaluate(node)

        return self.evaluator(node, comparison_adjective, group)

class MaxRankAdjective(_RankAdjective):
    def __init__(self, name: str, comparison_adjective_name: ComparisonAdjective, nodes_group_pointer_adjective_name: PointerAdjective):
        explanation = CompositeExplanation(
            RankAssumption('max', name, comparison_adjective_name, nodes_group_pointer_adjective_name),
            GroupComparison(comparison_adjective_name, nodes_group_pointer_adjective_name))
        evaluator = lambda node, comparison_adjective, group: all(comparison_adjective.evaluate(node, other_node) for other_node in group)
        super().__init__(name, comparison_adjective_name, nodes_group_pointer_adjective_name, explanation, evaluator)

class MinRankAdjective(_RankAdjective):
    def __init__(self, name: str, comparison_adjective_name: ComparisonAdjective, nodes_group_pointer_adjective_name: PointerAdjective):
        explanation = CompositeExplanation(
            RankAssumption('min', name, comparison_adjective_name, nodes_group_pointer_adjective_name),
            GroupComparison(comparison_adjective_name, nodes_group_pointer_adjective_name, positive_implication=False))
        evaluator = lambda node, comparison_adjective, group: all(comparison_adjective.evaluate(other_node, node) for other_node in group)
        super().__init__(name, comparison_adjective_name, nodes_group_pointer_adjective_name, explanation, evaluator)