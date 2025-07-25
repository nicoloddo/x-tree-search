from abc import ABC, abstractmethod
from typing import Any, Callable, List

from src.explainer.common.exceptions import CannotBeEvaluated

from src.explainer.propositional_logic import Proposition, Implies
from src.explainer.explanation import *
from src.explainer.framework import ArgumentationFramework
from src.explainer.common.validators import (
    validate_getter,
    validate_comparison_operator,
)
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
    """
    Abstract base class for all types of adjectives.

    This class defines the basic structure and methods for adjectives in the argumentation framework.
    """

    refer_to_nodes_as = None
    explanations_book = None

    def init_explanations_book(self):
        """Initialize the book keeping for all Adjective instances."""
        Adjective.explanations_book = {}

    def __init__(
        self,
        name: str,
        adjective_type: AdjectiveType,
        explanation: Explanation,
        tactics: List["Tactic"],
        *,
        definition: str,
        skip_statement: bool = False,
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the Adjective.

        :param name: The name of the adjective.
        :type name: str
        :param adjective_type: The type of the adjective (STATIC, POINTER, or RANKING).
        :type adjective_type: AdjectiveType
        :param explanation: A callable that takes a node and context and returns a Proposition.
        :type explanation: Explanation
        :param tactics: List of tactics to be applied to the adjective.
        :type tactics: List['Tactic']
        :param definition: The definition of the adjective, used to set the getter.
        :type definition: str
        :param skip_statement: Skip the consequent in the explanation of this adjective.
        :type skip_statement: bool, optional
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional

        :raises ValueError: If the name is an empty string.
        """
        if name == "":
            raise ValueError(
                "The name of Adjectives needs to have at least one character."
            )
        self.name = name
        self.type = adjective_type
        self.explanation = explanation
        self.framework = None
        self.definition = definition
        self.skip_statement = skip_statement

        if explain_with_adj_if is not None:
            if not isinstance(explain_with_adj_if[0], If):
                raise ValueError(
                    "The first element of the explain_with_adj_if parameter should be an If object."
                )
            if explain_with_adj_if[1] is None:
                raise ValueError(
                    "The second element of the explain_with_adj_if parameter should be a string."
                )
            if len(explain_with_adj_if) < 2 or len(explain_with_adj_if) > 3:
                raise ValueError(
                    "The explain_with_adj_if parameter should be a tuple with either two or three elements."
                )
            elif len(explain_with_adj_if) == 2:
                explain_with_adj_if = explain_with_adj_if + (None,)
        self.explain_with_adj_if = explain_with_adj_if

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
        if self.explain_with_adj_if is not None:
            self.explain_with_adj_if[0].contextualize(self)

        for tactic in self.explanation_tactics.values():
            tactic.contextualize(self)

    def decontextualize(self):
        """Undo the contextualization."""
        self.framework = None
        self.refer_to_nodes_as = None
        self.explanation.decontextualize()
        if self.explain_with_adj_if is not None:
            self.explain_with_adj_if[0].decontextualize()

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
            if tactic.name in self.explanation_tactics:
                # Count how many times tactic.name already exists in self.explanation_tactics
                count = sum(
                    1 for t in self.explanation_tactics if t.startswith(tactic.name)
                )

                # Append the count as an index to make the name unique
                tactic_name = f"{tactic.name}_{count}"
            else:
                tactic_name = tactic.name
            self.explanation_tactics[tactic_name] = tactic

    def _del_explanation_tactics(self, tactic_names):
        for tactic_name in tactic_names:
            del self.explanation_tactics[tactic_name]

    def get_explanation_tactic(self, tactic_name):
        return self.explanation_tactics[tactic_name]

    def list_explanation_tactics(self):
        for name, expl in self.explanation_tactics.items:
            print(f"{name}: {expl}")

    # evaluate, proposition, explain
    def evaluate(self, *args, explanation_tactics=None) -> Any:
        """
        Evaluate the adjective.
        If args are passed, evaluate in context.
        If not, this is just an implication inside abstract knowledge.

        Args:
            *args: Variable length argument list.

        Returns:
            The value of the adjective for the given node.
        """
        if args[0] is None:  # We are evaluating not in context
            return None
        else:
            try:
                evaluation = self._evaluate(*args)
            except AttributeError:
                raise CannotBeEvaluated(
                    self.name, args, self.framework.refer_to_nodes_as
                )
        evaluation = apply_explanation_tactics(
            self, "evaluation", explanation_tactics, evaluation
        )
        return evaluation

    @abstractmethod
    def _evaluate(self, *args, **kwargs) -> Any:
        pass

    def proposition(self, *args, explanation_tactics=None) -> Proposition:
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
        proposition = apply_explanation_tactics(
            self, "proposition", explanation_tactics, proposition
        )
        return proposition

    @abstractmethod
    def _proposition(self, *args, **kwargs) -> Proposition:
        pass

    def explain(
        self,
        node: Any,
        other_nodes: Any = None,
        *,
        explanation_tactics=None,
        current_explanation_depth,
        explain_further=True,
    ) -> Implies:
        """
        Provide an explanation for the adjective's value on a given node.

        Args:
            node: The node to explain the adjective for.
            other_node: The optional other node for Comparison Adjectives

        Returns:
            An Implies object representing the explanation.
        """
        if (
            self.explain_with_adj_if is not None
        ):  # Check if we need to reroute the explanation
            if self.explain_with_adj_if[0].condition_type == "comparison":
                self.framework.add_adjective(
                    AuxiliaryAdjective(
                        COMPARISON_AUXILIARY_ADJECTIVE, getter=lambda node: other_nodes
                    )
                )
            evaluation = self.explain_with_adj_if[0].evaluate(node)
            args = [node, other_nodes]
            kwargs = {
                "explanation_tactics": explanation_tactics,
                "current_explanation_depth": current_explanation_depth,
                "explain_further": explain_further,
            }
            if evaluation:
                adjective_to_explain = self.framework.get_adjective(
                    self.explain_with_adj_if[1]
                )
                return adjective_to_explain.explain(*args, **kwargs)
            else:
                if self.explain_with_adj_if[2] is not None:
                    adjective_to_explain = self.framework.get_adjective(
                        self.explain_with_adj_if[2]
                    )
                    return adjective_to_explain.explain(*args, **kwargs)

        if explanation_tactics is None:  # Check the explanation tactics
            explanation_tactics = {
                **self.explanation_tactics,
                **self.framework.general_explanation_tactics,
            }

        # Explain
        # Get propositions
        if self.type == AdjectiveType.COMPARISON:
            self.framework.add_adjective(
                AuxiliaryAdjective(
                    COMPARISON_AUXILIARY_ADJECTIVE, getter=lambda node: other_nodes
                )
            )
            evaluation = self.evaluate(
                node, other_nodes, explanation_tactics=explanation_tactics
            )
            consequent = self.proposition(
                evaluation, [node, other_nodes], explanation_tactics=explanation_tactics
            )
            if explain_further:
                antecedent = self.explanation.explain(
                    node,
                    explanation_tactics=explanation_tactics,
                    current_explanation_depth=current_explanation_depth,
                )
            else:
                antecedent = None
        else:
            evaluation = self.evaluate(node, explanation_tactics=explanation_tactics)
            consequent = self.proposition(
                evaluation, node, explanation_tactics=explanation_tactics
            )
            if explain_further:
                antecedent = self.explanation.explain(
                    node,
                    explanation_tactics=explanation_tactics,
                    current_explanation_depth=current_explanation_depth,
                )
            else:
                antecedent = None

        if antecedent is not None:  # If the explanation was given
            if self.skip_statement:  # If we should skip the consequent
                explanation = antecedent
                explanation_part = "antecedent"
            else:
                implication = Implies(antecedent, consequent)

                if self.framework.settings.print_depth:
                    implication._str_settings(
                        print_depth=self.framework.settings.print_depth
                    )

                explanation = implication
                explanation_part = "whole"
        else:  # There is no antecedent
            if self.skip_statement:  # If we should skip the consequent
                explanation = None
                explanation_part = "None"
            else:
                explanation = consequent
                explanation_part = "consequent"

        # Apply tactics
        if explanation is not None:
            explanation = apply_explanation_tactics(
                self,
                "explanation",
                explanation_tactics,
                explanation,
                explanation_part=explanation_part,
            )

        return explanation


class BooleanAdjective(Adjective):
    """Represents a boolean adjective."""

    def __init__(
        self,
        name: str,
        definition: str = DEFAULT_GETTER,
        explanation: Explanation | None = None,
        tactics: List["Tactic"] | None = None,
        *,
        skip_statement: bool = False,
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the BooleanAdjective.

        :param name: The name of the adjective.
        :type name: str
        :param definition: The correspondent node attribute (use the keyword "node" to refer to one of its elements).
        :type definition: str, optional
        :param explanation: An explanation for the adjective.
        :type explanation: Explanation | None, optional
        :param tactics: Tactics to use with the adjective.
        :type tactics: List['Tactic'] | None, optional
        :param skip_statement: Skip the consequent in the explanation of this adjective.
        :type skip_statement: bool, optional
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional
        """
        explanation = explanation or PossessionAssumption(name, definition)
        super().__init__(
            name,
            AdjectiveType.STATIC,
            explanation,
            tactics,
            definition=definition,
            skip_statement=skip_statement,
            explain_with_adj_if=explain_with_adj_if,
        )

    def _proposition(self, evaluation: bool = True, node: Any = None) -> Proposition:
        """Returns a proposition reflecting the adjective"""
        proposition = Proposition(node or self.refer_to_nodes_as, self.name, evaluation)
        return proposition

    def _evaluate(self, node: Any) -> bool:
        """
        Evaluate the boolean adjective for a given node.

        :param node: The node to evaluate.
        :type node: Any
        :return: The boolean value of the adjective for the given node.
        :rtype: bool
        :raises ValueError: If the getter doesn't return a boolean value.
        """
        if not isinstance(self.getter(node), bool):
            raise ValueError("Boolean adjectives should evaluate as a bool.")
        return self.getter(node)


class PointerAdjective(Adjective):
    """Represents a pointer adjective that references a specific attribute or object."""

    def __init__(
        self,
        name: str,
        definition: str = DEFAULT_GETTER,
        explanation: Explanation | None = None,
        tactics: List["Tactic"] | None = None,
        *,
        _custom_getter: Callable[[Any], Any] | None = None,
        skip_statement: bool = False,
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the PointerAdjective.

        :param name: The name of the adjective.
        :type name: str
        :param definition: The correspondent node attribute (use the keyword "node" to refer to one of its elements).
        :type definition: str, optional
        :param explanation: An explanation for the adjective.
        :type explanation: Explanation | None, optional
        :param tactics: Tactics to use with the adjective.
        :type tactics: List['Tactic'] | None, optional
        :param _custom_getter: Parameter to use for internal scopes, can override the getter attribute of the adjective.
                               It is suggested to not use externally.
        :type _custom_getter: Callable[[Any], Any] | None, optional
        :param skip_statement: Skip the consequent in the explanation of this adjective.
        :type skip_statement: bool, optional
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional
        """
        explanation = explanation or PossessionAssumption(name, definition)
        super().__init__(
            name,
            AdjectiveType.POINTER,
            explanation,
            tactics,
            definition=definition,
            skip_statement=skip_statement,
            explain_with_adj_if=explain_with_adj_if,
        )
        if _custom_getter is not None:
            self.getter = _custom_getter

    def _proposition(self, evaluation: Any = None, node: Any = None) -> Proposition:
        """Returns a proposition reflecting the pointer value"""
        proposition = Proposition(node or self.refer_to_nodes_as, self.name, evaluation)
        return proposition

    def _evaluate(self, node: Any) -> Any:
        """
        Evaluate the pointer adjective for a given node.

        :param node: The node to evaluate.
        :type node: Any
        :return: The value pointed to by the adjective for the given node.
        :rtype: Any
        """
        if type(node) is list:
            return [self.getter(element) for element in node]
        else:
            return self.getter(node)


class QuantitativePointerAdjective(PointerAdjective):
    pass


class AuxiliaryAdjective(PointerAdjective):
    """Auxiliary Adjectives are created dynamically during explanations. They have as getter a queue system."""

    def __init__(self, name: str, getter: Callable[[Any], Any]):
        """
        Initialize the AuxiliaryAdjective.

        :param name: The name of the adjective.
        :type name: str
        :param getter: The initial getter function for the adjective.
        :type getter: Callable[[Any], Any]
        """
        super().__init__(name, _custom_getter=getter)
        self.getter = [self.getter]
        self.type = AdjectiveType.AUXILIARY
        self.empty = False

    def add_getter(self, new_getter: Callable[[Any], Any]):
        """
        Add a new getter to the queue.

        :param new_getter: The new getter function to add.
        :type new_getter: Callable[[Any], Any]
        """
        self.getter.append(new_getter)
        self.empty = False

    def _evaluate(self, node: Any) -> Any:
        """
        Evaluate the auxiliary adjective for a given node.

        :param node: The node to evaluate.
        :type node: Any
        :return: The result of applying the current getter to the node.
        :rtype: Any
        :raises CannotBeEvaluated: If the getter queue is empty.
        """
        if self.empty:
            raise CannotBeEvaluated(
                f"the Auxiliary Adjective {self.name} is empty while evaluating {Proposition.format_node(node)}."
            )
        current_getter = (
            self.getter.pop()
        )  # The auxiliary adjective can be evaluated only as many times it was declared
        if len(self.getter) == 0:
            self.empty = True
        return current_getter(node)


class NodesGroupPointerAdjective(PointerAdjective):
    """
    Represents a pointer adjective that references a group of objects.
    You can specify an object to not include from the group definition through the "excluding" parameter.
    Example:
        NodesGroupPointerAdjective("siblings", definition = "node.parent.children", excluding = "node")
    """

    def __init__(
        self,
        name: str,
        definition: str = DEFAULT_GETTER,
        explanation: Explanation | None = None,
        tactics: List["Tactic"] | None = None,
        *,
        excluding: str = "",
    ):
        """
        Initialize the NodesGroupPointerAdjective.

        :param name: The name of the adjective.
        :type name: str
        :param definition: The definition of the group.
        :type definition: str, optional
        :param explanation: An explanation for the adjective.
        :type explanation: Explanation | None, optional
        :param tactics: Tactics to use with the adjective.
        :type tactics: List['Tactic'] | None, optional
        :param excluding: An object to exclude from the group definition.
        :type excluding: str, optional
        """
        explanation = explanation or PossessionAssumption(
            name, definition + " excluding " + excluding
        )
        if excluding:
            composite_definition = (
                f"[element for element in {definition} if element is not {excluding}]"
            )
        else:
            composite_definition = f"[{definition}]"
        super().__init__(name, composite_definition, explanation, tactics)

    def _proposition(self, evaluation: Any = None, node: Any = None) -> Proposition:
        """
        Returns a proposition reflecting the pointer value.

        :param evaluation: The evaluated value of the adjective.
        :type evaluation: Any, optional
        :param node: The node for which the proposition is created.
        :type node: Any, optional
        :return: A proposition reflecting the pointer value.
        :rtype: Proposition
        :raises ValueError: If the evaluation is not a list.
        """
        if evaluation is not None and type(evaluation) is not list:
            raise ValueError(
                f"{self.name} NodesGroupPointerAdjective should evaluate to a list. Check your definition."
            )

        proposition = Proposition(node or self.refer_to_nodes_as, self.name, evaluation)
        return proposition


class ComparisonAdjective(Adjective):
    """
    Represents a ranking adjective used for comparing nodes.
    Comparison nodes do not need a getter to be evaluated.

    While explaining a Comparison Adjective you can refer to an auxiliary adjective called "compared to".
    """

    def __init__(
        self,
        name: str,
        property_pointer_adjective_name: str,
        operator: str,
        *,
        stop_if_found_adjectives: List[str] = None,
        explanation: Explanation | None = None,
        tactics: List["Tactic"] | None = None,
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the ComparisonAdjective.

        :param name: The name of the adjective.
        :type name: str
        :param property_pointer_adjective_name: The name of the pointer adjective to use for comparison.
        :type property_pointer_adjective_name: str
        :param stop_if_found_adjectives: The pointer adjective names that can stop recursion of comparisons when the property is a node pointer adjective.
                                                                For example, you may want to stop comparing nodes of nodes when one is a final node:
                                                                node 1 is better than node 2 (because node 1 leads to node 3 and node 2 leads to node 4,
                                                                and node 3 is a loss).
                                                                Without a stopper, the explanation would continue saying:
                                                                and node 4 is better than node 3 because node 4 leads to node 5 and node 3 is a loss. And so on.
        :type stop_if_found_adjectives: List[str]
        :param operator: A string with the boolean operator to utilize.
        :type operator: str
        :param explanation: An explanation for the comparison result. Do not provide to use the default explanation.
        :type explanation: Explanation | None, optional
        :param tactics: Tactics for the adjective, refer to the main Adjective class.
        :type tactics: List['Tactic'] | None, optional
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional
        """
        if explanation is None:
            explanation = CompositeExplanation(
                ComparisonAssumption(name, property_pointer_adjective_name, operator),
                ComparisonNodesPropertyPossession(
                    property_pointer_adjective_name,
                    stop_if_found_adjectives,
                ),
            )
        else:
            print(
                "Warning: Using a custom explanation might not be compatible with some explanation tactics."
            )
        super().__init__(
            name,
            AdjectiveType.COMPARISON,
            explanation,
            tactics,
            definition=DEFAULT_GETTER,
            explain_with_adj_if=explain_with_adj_if,
        )
        self.property_pointer_adjective_name = property_pointer_adjective_name

        # Validate the operator to ensure it's safe and expected
        validate_comparison_operator(operator)
        # Construct and return the lambda function
        self.comparison_operator = eval(f"lambda x, y: x {operator} y")

        self.operator = operator

    def _proposition(self, evaluation: bool = True, nodes: Any = None) -> Proposition:
        """Returns a proposition reflecting the comparison"""
        if nodes == None:
            nodes = [f"{self.refer_to_nodes_as}1", f"{self.refer_to_nodes_as}2"]

        main_node = nodes[0]
        other_nodes = nodes[1]

        if type(other_nodes) is not list:
            other_nodes = [other_nodes]

        proposition = Proposition(main_node, self.name, evaluation, object=other_nodes)

        return proposition

    def _evaluate(self, node1: Any, other_nodes: Any) -> bool:
        """
        Evaluate the comparison between two nodes.

        :param node1: The first node to compare.
        :type node1: Any
        :param other_nodes: The other nodes to compare to the first one.
        :type other_nodes: Any
        :return: A boolean indicating how node1 compares to node2 with the given operator.
        :rtype: bool
        :raises SyntaxError: If the ComparisonAdjective is linked to a non-quantitative adjective.
        """
        property_pointer_adjective = self.framework.get_adjective(
            self.property_pointer_adjective_name
        )

        if not isinstance(property_pointer_adjective, QuantitativePointerAdjective):
            raise SyntaxError(
                f"ComparisonAdjective has been linked to a non quantitative adjective {property_pointer_adjective.name}."
            )

        value1 = property_pointer_adjective.evaluate(node1)

        if type(other_nodes) is not list:
            other_nodes = [other_nodes]
        other_values = [
            property_pointer_adjective.evaluate(node2) for node2 in other_nodes
        ]

        try:
            return all(
                [self.comparison_operator(value1, value2) for value2 in other_values]
            )
        except TypeError:
            raise CannotBeEvaluated(
                message_override=f'the comparison "{self.name}" cannot be evaluated: some of the {self.framework.refer_to_nodes_as}s in the comparison don\'t have a {self.property_pointer_adjective_name}.'
            )

    def get_true_group(self, node1: Any, other_nodes: Any) -> Any:
        """
        Get the group of nodes that satisfy the comparison adjective.

        :param node1: The first node to compare.
        :type node1: Any
        :param other_nodes: The other nodes to compare to the first one.
        :type other_nodes: Any
        :return: A list of nodes that satisfy the comparison adjective.
        :rtype: Any
        """
        property_pointer_adjective = self.framework.get_adjective(
            self.property_pointer_adjective_name
        )
        value1 = property_pointer_adjective.evaluate(node1)

        if type(other_nodes) is not list:
            other_nodes = [other_nodes]
        other_values = [
            property_pointer_adjective.evaluate(node2) for node2 in other_nodes
        ]

        return [
            other_node
            for other_node in other_nodes
            if self.comparison_operator(
                value1, other_values[other_nodes.index(other_node)]
            )
        ]


class _RankAdjective(BooleanAdjective):
    """
    Represents a static (boolean) adjective that specifically refers to the
    property of being x ranked in a group, based on a given comparison adjective
    and the evaluator function. This is parent class of MaxRankAdjective and MinRankAdjective.
    """

    def __init__(
        self,
        name: str,
        comparison_adjective_names: List[str],
        group_pointer_adjective_name: str,
        explanation: Explanation,
        tactics: List["Tactic"],
        evaluator: Callable[[Any, ComparisonAdjective, PointerAdjective], bool],
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the _RankAdjective.
        Evaluates to true if any of the comparison adjectives is true for the node when compared to all the other nodes in the group.

        :param name: The name of the adjective.
        :type name: str
        :param comparison_adjective_names: The names of the comparison adjectives.
        :type comparison_adjective_names: List[str]
        :param group_pointer_adjective_name: The name of the group pointer adjective.
        :type group_pointer_adjective_name: str
        :param explanation: An explanation for the adjective.
        :type explanation: Explanation | None, optional
        :param tactics: Tactics for the adjective.
        :type tactics: List['Tactic'] | None, optional
        :param evaluator: A function to evaluate the rank.
        :type evaluator: Callable[[Any, ComparisonAdjective, PointerAdjective], bool]
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional
        """
        explanation = explanation or PossessionAssumption(name)
        super().__init__(
            name,
            explanation=explanation,
            tactics=tactics,
            explain_with_adj_if=explain_with_adj_if,
        )
        self.comparison_adjective_names = comparison_adjective_names
        self.group_pointer_adjective_name = group_pointer_adjective_name
        self.evaluator = evaluator

    def _evaluate(self, node: Any) -> bool:
        """
        Evaluate the static adjective for a given node.

        :param node: The node to evaluate.
        :type node: Any
        :return: The boolean result of the rank evaluation.
        :rtype: bool
        """
        comparison_adjectives = [
            self.framework.get_adjective(comparison_adjective_name)
            for comparison_adjective_name in self.comparison_adjective_names
        ]

        group = self.framework.get_adjective(
            self.group_pointer_adjective_name
        ).evaluate(node)

        return self.evaluator(node, comparison_adjectives, group)


class MaxRankAdjective(_RankAdjective):
    def __init__(
        self,
        name: str,
        comparison_adjective_names: List[str],
        nodes_group_pointer_adjective_name: str,
        tactics: List["Tactic"] | None = None,
        *,
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the MaxRankAdjective.
        Evaluates to true if any of the comparison adjectives is true for the node when compared to all the other nodes in the group.

        :param name: The name of the adjective.
        :type name: str
        :param comparison_adjective_names: The names of the comparison adjectives.
        :type comparison_adjective_names: List[str]
        :param nodes_group_pointer_adjective_name: The name of the nodes group pointer adjective.
        :type nodes_group_pointer_adjective_name: str
        :param tactics: Tactics for the adjective.
        :type tactics: List['Tactic'] | None, optional
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional
        """
        explanation = CompositeExplanation(
            RankAssumption(
                "max",
                name,
                comparison_adjective_names,
                nodes_group_pointer_adjective_name,
            ),
            GroupComparison(
                comparison_adjective_names, nodes_group_pointer_adjective_name
            ),
        )
        evaluator = lambda node, comparison_adjectives, group: all(
            any(
                comparison.evaluate(node, other_node)
                for comparison in comparison_adjectives
            )
            for other_node in group
        )
        super().__init__(
            name,
            comparison_adjective_names,
            nodes_group_pointer_adjective_name,
            explanation,
            tactics,
            evaluator,
            explain_with_adj_if=explain_with_adj_if,
        )


class MinRankAdjective(_RankAdjective):
    def __init__(
        self,
        name: str,
        comparison_adjective_names: List[str],
        nodes_group_pointer_adjective_name: str,
        tactics: List["Tactic"] | None = None,
        *,
        explain_with_adj_if: tuple[If, str, str | None] = None,
    ):
        """
        Initialize the MinRankAdjective.
        Evaluates to true if any of the comparison adjectives is true for the node when compared to all the other nodes in the group.

        :param name: The name of the adjective.
        :type name: str
        :param comparison_adjective_names: The names of the comparison adjectives used for ranking.
        :type comparison_adjective_names: List[str]
        :param nodes_group_pointer_adjective_name: The name of the pointer adjective that references the group of nodes to compare.
        :type nodes_group_pointer_adjective_name: str
        :param tactics: List of tactics to be applied to the adjective, optional.
        :type tactics: List['Tactic'] | None
        :param explain_with_adj_if: A tuple with an If object, a first adjective name and a second, optional, adjective name.
            If the parameter is provided and the If is True, the explanation will be given with the first adjective provided, else with the second.
        :type explain_with_adj_if: tuple[If, str, str | None] | None, optional

        The MinRankAdjective represents the property of having the minimum rank
        within a group based on a given comparison adjective.
        """
        explanation = CompositeExplanation(
            RankAssumption(
                "min",
                name,
                comparison_adjective_names,
                nodes_group_pointer_adjective_name,
            ),
            GroupComparison(
                comparison_adjective_names,
                nodes_group_pointer_adjective_name,
                positive_implication=False,
            ),
        )
        evaluator = lambda node, comparison_adjectives, group: all(
            any(
                comparison.evaluate(other_node, node)
                for comparison in comparison_adjectives
            )
            for other_node in group
        )
        super().__init__(
            name,
            comparison_adjective_names,
            nodes_group_pointer_adjective_name,
            explanation,
            tactics,
            evaluator,
            explain_with_adj_if=explain_with_adj_if,
        )
