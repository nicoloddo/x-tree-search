from abc import ABC, abstractmethod
from typing import Any, Callable, List

from src.explainer.common.exceptions import CannotBeEvaluated

from src.explainer.propositional_logic import Proposition, Implies
from src.explainer.explanation import *
from src.explainer.framework import ArgumentationFramework
from src.explainer.common.validators import validate_getter, validate_comparison_operator
from src.explainer.common.utils import AdjectiveType, apply_explanation_tactics

"""
Adjectives constitute predicates by getting attributed to a node.
Only nodes can have adjectives.
A predicate in the Framework looks like:
node is <adjective> (BooleanAdjective)
node has <adjective> = value (PointerAdjective)
node <adjective> than node2 (RankingAdjective)
"""

DEFAULT_GETTER = "node.no_getter_provided"
COMPARISON_AUXILIARY_ADJECTIVE = "compared to"
Explanation.COMPARISON_AUXILIARY_ADJECTIVE = COMPARISON_AUXILIARY_ADJECTIVE

class Adjective(ABC):
    """Abstract base class for all types of adjectives."""
    refer_to_nodes_as = None
    explanations_book = None
    def init_explanations_book(self): # Initialize the book keeping for all Adjective instances
        Adjective.explanations_book = {}

    def __init__(self, name: str, adjective_type: AdjectiveType, explanation: Explanation, tactics: List['Tactic'], *, definition: str):
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
        if name == '':
            raise ValueError("The name of Adjectives needs to have at least one character.")
        self.name = name
        self.type = adjective_type
        self.explanation = explanation
        self.framework = None
        self.definition = definition
        self.getter = None
        self.set_getter(definition)

        self.explanation_tactics = {}
        if tactics is None:
            tactics = []
        self.add_explanation_tactics(tactics)

    # Utility methods
    def _set_getter(self, getter: Callable[[Any], Any]):
        self.getter = getter

    def set_getter(self, getter: str):
        """ 
        Contextualizes the adjective onto the current tree by specifying
        the getter function that permits to evaluate the adjective.
        """
        validate_getter(getter)
        self._set_getter(eval(f"lambda node: {getter}"))

    def contextualize(self, framework: ArgumentationFramework):
        """Sets the Argumentation framework the Adjective belongs to."""
        self.framework = framework
        self.refer_to_nodes_as = self.framework.refer_to_nodes_as
        self.explanation.contextualize(self)

        for tactic in self.explanation_tactics.values():
            tactic.contextualize(self)
    
    def decontextualize(self):
        """Undo the contextualization."""
        self.framework = None
        self.refer_to_nodes_as = None
        self.explanation.decontextualize()

        for tactic in self.explanation_tactics.values():
            tactic.decontextualize()

    def add_explanation_tactics(self, tactics):
        for tactic in tactics:
            self.add_explanation_tactic(tactic)
    
    def add_explanation_tactic(self, tactic):
        tactics_to_add = [tactic]
        tactics_to_add += tactic.get_requirements()
        self._add_explanation_tactics(tactics_to_add)

    def _add_explanation_tactics(self, tactics):
        for tactic in tactics:
            tactic.contextualize(self)
            self.explanation_tactics[tactic.name] = tactic
    
    def _del_explanation_tactics(self, tactic_names):
        for tactic_name in tactic_names:
            del self.explanation_tactics[tactic_name]
        
    def get_explanation_tactic(self, tactic_name):
        return self.explanation_tactics[tactic_name]

    # evaluate, proposition, implies, explain
    def evaluate(self, *args, explanation_tactics = None) -> Any:
        """
        Evaluate the adjective.
        If args are passed, evaluate in context.
        If not, this is just an implication inside abstract knowledge.
        
        Args:
            *args: Variable length argument list.
        
        Returns:
            The value of the adjective for the given node.
        """
        if args[0] is None: # We are evaluating not in context
            return None
        else:
            try:
                evaluation = self._evaluate(*args)
            except AttributeError:
                raise CannotBeEvaluated(self.name, args, self.framework.refer_to_nodes_as)        
        evaluation = apply_explanation_tactics(self, "evaluation", explanation_tactics, evaluation)
        return evaluation

    @abstractmethod
    def _evaluate(self, *args, **kwargs) -> Any:
        pass

    def proposition(self, *args, explanation_tactics = None) -> Proposition:
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
        self.refer_to_nodes_as = self.framework.refer_to_nodes_as
        proposition = self._proposition(*args)
        proposition = apply_explanation_tactics(self, "proposition", explanation_tactics, proposition)
        return proposition
    
    @abstractmethod
    def _proposition(self, *args, **kwargs) -> Proposition:
        pass

    def explain(self, node: Any, other_nodes: Any = None, *, explanation_tactics = None, current_explanation_depth, explain_further=True) -> Implies:
        """
        Provide an explanation for the adjective's value on a given node.
        
        Args:
            node: The node to explain the adjective for.
            other_node: The optional other node for Comparison Adjectives
        
        Returns:
            An Implies object representing the explanation.
        """
        if explanation_tactics is None:
            explanation_tactics = {**self.explanation_tactics, **self.framework.general_explanation_tactics}

        # Get propositions
        if self.type == AdjectiveType.COMPARISON:
            self.framework.add_adjective(AuxiliaryAdjective(COMPARISON_AUXILIARY_ADJECTIVE, getter = lambda node: other_nodes))
            evaluation = self.evaluate(node, other_nodes, explanation_tactics=explanation_tactics)
            consequent = self.proposition(evaluation, [node, other_nodes], explanation_tactics=explanation_tactics)
            if explain_further:
                antecedent = self.explanation.explain(node, explanation_tactics=explanation_tactics, current_explanation_depth=current_explanation_depth)
            else:
                antecedent = None
            #self.framework.del_adjective(COMPARISON_AUXILIARY_ADJECTIVE)
        else:
            evaluation = self.evaluate(node, explanation_tactics=explanation_tactics)
            consequent = self.proposition(evaluation, node, explanation_tactics=explanation_tactics)
            if explain_further:
                antecedent = self.explanation.explain(node, explanation_tactics=explanation_tactics, current_explanation_depth=current_explanation_depth)
            else:
                antecedent = None

        if antecedent is not None: # If the explanation was given
            implication = Implies(antecedent, consequent)

            if self.framework.settings.print_depth:
                implication._str_settings(print_depth = self.framework.settings.print_depth)

            explanation = implication
            explanation_part = 'whole'
        else:
            explanation = consequent
            explanation_part = 'consequent'
        
        explanation = apply_explanation_tactics(self, "explanation", explanation_tactics, explanation, explanation_part=explanation_part)

        # Save the explanations in a lookup table
        book_record = {'adjective': self, 'node': node, 'evaluation': evaluation, 'explanation': explanation, 'depth': current_explanation_depth}
        if self.name not in self.explanations_book:
            self.explanations_book[self.name] = [book_record]
        else:
            self.explanations_book[self.name].append(book_record)

        return explanation
        
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

class BooleanAdjective(Adjective):
    """Represents a boolean adjective."""
    
    def __init__(self, name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None, tactics = None):
        """
        Initialize the BooleanAdjective.
        
        Args:
            name: The name of the adjective.
            definition: The correspondant node attribute (use the keyword "node" to refer to one of its elements).
            explanation: An explanation for the adjective.
        """
        explanation = explanation or PossessionAssumption(name, definition)
        super().__init__(name, AdjectiveType.STATIC, explanation, tactics, definition = definition)

    def _proposition(self, evaluation: bool = True, node: Any = None) -> Proposition:
        """ Returns a proposition reflecting the adjective """
        proposition = Proposition(node or self.refer_to_nodes_as, self.name, evaluation)
        return proposition

    def _evaluate(self, node: Any) -> bool:
        """Evaluate the boolean adjective for a given node."""
        if not isinstance(self.getter(node), bool):
            raise ValueError("Boolean adjectives should evaluate as a bool.")
        return self.getter(node)

class PointerAdjective(Adjective):
    """Represents a pointer adjective that references a specific attribute or object."""
    
    def __init__(self, name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None, tactics = None, *, _custom_getter = None):
        """
        Initialize the PointerAdjective.
        
        Args:
            name: The name of the adjective.
            definition: The correspondant node attribute (use the keyword "node" to refer to one of its elements).
            explanation: An explanation for the adjective.
            tactics: Tactics to use with the adjective.
            _custom_getter: Parameter to use for internal scopes, can override the getter attribute of the adjective.
                            It is suggested to not use externally.
        """
        explanation = explanation or PossessionAssumption(name, definition)
        super().__init__(name, AdjectiveType.POINTER, explanation, tactics, definition = definition)
        if _custom_getter is not None:
            self.getter = _custom_getter

    def _proposition(self, evaluation: Any = None, node: Any = None) -> Proposition:
        """ Returns a proposition reflecting the pointer value """
        proposition = Proposition(node or self.refer_to_nodes_as, self.name, evaluation)
        return proposition

    def _evaluate(self, node: Any) -> Any:
        """Evaluate the pointer adjective for a given node."""
        return self.getter(node)

class QuantitativePointerAdjective(PointerAdjective):
    pass

class AuxiliaryAdjective(PointerAdjective):
    """Auxiliary Adjectives are created dynamically during explanations. They have as getter a queue system."""
    def __init__(self, name, getter):
        super().__init__(name, _custom_getter = getter)
        self.getter = [self.getter]
        self.type = AdjectiveType.AUXILIARY
        self.empty = False

    def add_getter(self, new_getter):            
        self.getter.append(new_getter)
        self.empty = False
    
    def _evaluate(self, node: Any):
        if self.empty:
            ValueError(f"The Auxiliary Adjective {self.name} is empty while evaluating {node}.")
        current_getter = self.getter.pop()
        if len(self.getter) == 0:
            self.empty = True
        return current_getter(node)

class NodesGroupPointerAdjective(PointerAdjective):
    """Represents a pointer adjective that references a group of objects. 
    You can specify an object to not include from the group definition through the "excluding" parameter.
    Example:
        NodesGroupPointerAdjective("siblings", definition = "node.parent.children", excluding = "node")
    """
    def __init__(self, name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None, tactics = None, *, excluding: str):
        explanation = explanation or PossessionAssumption(name, definition + " excluding " + excluding)
        if excluding:
            composite_definition = f"[element for element in {definition} if element is not {excluding}]"
        else:
            composite_definition = f"[{definition}]"
        super().__init__(name, composite_definition, explanation, tactics)
    
    def _proposition(self, evaluation: Any = None, node: Any = None) -> Proposition:
        if evaluation is not None and type(evaluation) is not list:
            raise ValueError(f"{self.name} NodesGroupPointerAdjective should evaluate to a list. Check your definition.")

        """ Returns a proposition reflecting the pointer value """
        proposition = Proposition(node or self.refer_to_nodes_as, self.name, evaluation)
        return proposition

class ComparisonAdjective(Adjective):
    """Represents a ranking adjective used for comparing nodes.
    Comparison nodes do not need a getter to be evaluated.
    
    While explaining a Comparison Adjective you can refer to an auxiliary adjective called "compared to".
    """
    
    def __init__(self, name: str, property_pointer_adjective_name: str, operator: str, *, explanation = None, tactics = None):
        """
        Initialize the RankingAdjective.
        
        Args:
            name: The name of the adjective.
            property_pointer_adjective_name: The name of the pointer adjective to use for comparison.
            operator: A string with the boolean operator to utilize.
            explanation: An explanation for the comparison result. Do not provide to use the default explanation.
            tactics: Tactics for the adjective, refer to the main Adjective class.
        """
        if explanation is None:
            explanation = CompositeExplanation(
                ComparisonAssumption(name, property_pointer_adjective_name, operator),
                ComparisonNodesPropertyPossession(property_pointer_adjective_name))
        super().__init__(name, AdjectiveType.COMPARISON, explanation, tactics, definition=DEFAULT_GETTER)
        self.property_pointer_adjective_name = property_pointer_adjective_name

        # Validate the operator to ensure it's safe and expected
        validate_comparison_operator(operator)
        # Construct and return the lambda function
        self.comparison_operator = eval(f"lambda x, y: x {operator} y")
            
        self.operator = operator

    def _proposition(self, evaluation: bool = True, nodes: Any = None) -> Proposition:
        """ Returns a proposition reflecting the comparison """
        if nodes == None:
            nodes = [f"{self.refer_to_nodes_as}1", f"{self.refer_to_nodes_as}2"]

        main_node = nodes[0]
        other_nodes = nodes[1]

        if type(other_nodes) is not list:
            other_nodes = [other_nodes]

        other_nodes_string = ', '.join([str(node) for node in other_nodes])

        proposition = Proposition(main_node, f"{self.name} {other_nodes_string}", evaluation)

        return proposition

    def _evaluate(self, node1: Any, other_nodes: Any) -> bool:
        """
        Evaluate the comparison between two nodes.
        
        Args:
            node1: The first node to compare.
            other_nodes: The other nodes to compare to the first one.
        
        Returns:
            A boolean indicating how node1 compares to node2 with the given operator.
        """
        property_pointer_adjective = self.framework.get_adjective(self.property_pointer_adjective_name)

        if not isinstance(property_pointer_adjective, QuantitativePointerAdjective):
            raise SyntaxError(f"ComparisonAdjective has been linked to a non quantitative adjective {property_pointer_adjective.name}.")
        
        value1 = property_pointer_adjective.evaluate(node1)

        if type(other_nodes) is not list:
            other_nodes = [other_nodes]
        other_values = [property_pointer_adjective.evaluate(node2) for node2 in other_nodes]
                        
        return all([self.comparison_operator(value1, value2) for value2 in other_values])

class _RankAdjective(BooleanAdjective):
    """Represents a static (boolean) adjective that specifically refers to the
    property of being x ranked in a group, based on a given comparison adjective
    and the evaluator function. This is parent class of MaxRankAdjective and MinRankAdjective."""
    
    def __init__(self, name: str, comparison_adjective_name: str, group_pointer_adjective_name: str, explanation: Explanation, tactics: List['Tactic'], evaluator: Callable[[Any, ComparisonAdjective, PointerAdjective], bool]):
        """
        Initialize the MaxRankAdjective.
        
        Args:
            name: The name of the adjective.
            comparison_adjective:
            group_pointer_adjective:
        """
        explanation = explanation or PossessionAssumption(name)
        super().__init__(name, explanation=explanation, tactics=tactics)
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name
        self.evaluator = evaluator

    def _evaluate(self, node: Any) -> bool:
        """Evaluate the static adjective for a given node."""
        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)

        group = self.framework.get_adjective(self.group_pointer_adjective_name).evaluate(node)

        return self.evaluator(node, comparison_adjective, group)

class MaxRankAdjective(_RankAdjective):
    def __init__(self, name: str, comparison_adjective_name: ComparisonAdjective, nodes_group_pointer_adjective_name: PointerAdjective, tactics = None):
        explanation = CompositeExplanation(
            RankAssumption('max', name, comparison_adjective_name, nodes_group_pointer_adjective_name),
            GroupComparison(comparison_adjective_name, nodes_group_pointer_adjective_name))
        evaluator = lambda node, comparison_adjective, group: all(comparison_adjective.evaluate(node, other_node) for other_node in group)
        super().__init__(name, comparison_adjective_name, nodes_group_pointer_adjective_name, explanation, tactics, evaluator)

class MinRankAdjective(_RankAdjective):
    def __init__(self, name: str, comparison_adjective_name: ComparisonAdjective, nodes_group_pointer_adjective_name: PointerAdjective, tactics = None):
        explanation = CompositeExplanation(
            RankAssumption('min', name, comparison_adjective_name, nodes_group_pointer_adjective_name),
            GroupComparison(comparison_adjective_name, nodes_group_pointer_adjective_name, positive_implication=False))
        evaluator = lambda node, comparison_adjective, group: all(comparison_adjective.evaluate(other_node, node) for other_node in group)
        super().__init__(name, comparison_adjective_name, nodes_group_pointer_adjective_name, explanation, tactics, evaluator)