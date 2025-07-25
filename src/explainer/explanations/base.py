from abc import ABC, abstractmethod
from typing import Any

from src.explainer.propositional_logic import LogicalExpression


class Explanation(ABC):
    refer_to_nodes_as = None
    COMPARISON_AUXILIARY_ADJECTIVE = None

    """Abstract base class for all types of explanations."""

    def __init__(self):
        self.explanation_tactics = {}
        self.explanation_of_adjective = None
        self.framework = None

    def contextualize(self, adjective: "Adjective"):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.explanation_of_adjective = adjective
        self.framework = adjective.framework
        self.refer_to_nodes_as = self.framework.refer_to_nodes_as
        self._contextualize()

    def decontextualize(self):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.explanation_of_adjective = None
        self.framework = None
        self.refer_to_nodes_as = None
        self._decontextualize()

    def _contextualize(self, *args, **kwargs):
        pass

    def _decontextualize(self, *args, **kwargs):
        pass

    def explain(
        self,
        node: Any,
        *,
        explanation_tactics=None,
        current_explanation_depth,
        explain_further=True
    ) -> LogicalExpression:
        """
        Generate a propositional logic explanation for the given node.

        Args:
            node: The node to explain.
            other_nodes: Other nodes in case of multiple node explanations (e.g. comparisons)
            explanation_tactics: Optional explanation tactics to be handled
            current_explanation_depth: The amount of explanations that were given
                                during the current explanation cycle

        Returns:
            A LogicalExpression representing the explanation.
        """

        self.current_explanation_depth = current_explanation_depth
        self.explanation_tactics = explanation_tactics or {}

        if current_explanation_depth > self.framework.settings.explanation_depth:
            return

        explanation = self._explain(node)

        if explanation is not None:
            # We assign to this explanation the current explanation depth so that Implies
            # can be indented well depending on the depth.
            explanation.current_explanation_depth = current_explanation_depth

            record = {
                "explanation_of_adjective": self.explanation_of_adjective.name,
                "adjective_ref": self.explanation_of_adjective,
                "node": node,
                "explanation_type": type(self),
                "depth": current_explanation_depth,
            }
            explanation.set_record(record)

            if not explain_further:
                explanation = explanation.consequent
            return explanation
        else:
            return

    def forward_explanation(self, obj, *args, explain_further=True, no_increment=False):
        increment = 0 if no_increment else 1
        # if isinstance(obj, Adjective):
        # return adjective.explain(*args, current_explanation_depth = self.current_explanation_depth + increment)
        return obj.explain(
            *args,
            explanation_tactics=self.explanation_tactics,
            current_explanation_depth=self.current_explanation_depth + increment,
            explain_further=explain_further
        )

    def forward_multiple_explanations(
        self, *forward_explanations, explain_further=True, no_increment=False
    ):
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
        explanation_tactics = self.explanation_tactics

        explanations = []
        for obj, *args in forward_explanations:
            explanation = obj.explain(
                *args,
                explanation_tactics=explanation_tactics,
                current_explanation_depth=forward_explanation_depth,
                explain_further=explain_further
            )
            explanations.append(explanation)

        return explanations

    def forward_evaluation(self, obj, *args):
        return obj.evaluate(*args, explanation_tactics=self.explanation_tactics)

    def forward_multiple_evaluations(self, *forward_evaluations):
        """
        Handle multiple forward evaluations with variable arguments and return an array of evaluations.
        Make sure to use this forwarding method to correctly forward explanation tactics.

        Args:
        *forward_evaluations: Variable number of tuples. Each tuple should contain:
                    (obj, *args) with
                    obj: is the Adjective or Explanation object from which to forward the explanation,
                    *args: are the arguments to pass to object.evaluate.

        Returns:
        list: An array of evaluations returned by each obj.evaluate call.
        """
        explanation_tactics = self.explanation_tactics

        evaluations = []
        for obj, *args in forward_evaluations:
            evaluation = obj.evaluate(*args, explanation_tactics=explanation_tactics)
            evaluations.append(evaluation)

        return evaluations

    @abstractmethod
    def _explain(self, node: Any) -> LogicalExpression:
        pass
