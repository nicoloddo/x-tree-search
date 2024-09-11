from .base import Explanation
from .simple_explanation import Possession

from src.explainer.propositional_logic import Postulate, LogicalExpression, And, Or

from src.explainer.common.utils import apply_explanation_tactics

from typing import Any

class If(Possession):
    """
    Represents a condition based on an adjective's value.
    If provided with a pointer_adjective_name, the condition is based on the
    value stored at the pointer. If not, the condition is based on the self node.

    When not provided with a value, 
    the condition is simply checked as a static adjective (boolean)
    """

    def __init__(self, *args, value: Any = True, explain_further=True, forward_pointers_explanations=True):
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
        self.explain_further=explain_further
        self.forward_pointers_explanations=forward_pointers_explanations
    
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

    def evaluate(self, node: Any, explanation_tactics = None) -> bool:
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
            obj_under_evaluation = self.forward_evaluation(pointer_adjective, node)

        adjective = self.framework.get_adjective(self.adjective_name)
        evaluation = adjective.evaluate(obj_under_evaluation) == self.value
        return evaluation

class ConditionalExplanation(Explanation):
    """Represents an explanation that depends on a condition."""
    
    def __init__(self, *, condition: If, explanation_if_true: Explanation, explanation_if_false: Explanation, skip_condition_statement: bool = False, skip_condition_statement_if_true: bool = False, skip_condition_statement_if_false: bool = False):
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
        self.skip_condition_statement = skip_condition_statement
        self.skip_condition_statement_if_true = skip_condition_statement_if_true
        self.skip_condition_statement_if_false = skip_condition_statement_if_false

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
        
        Args:
            node: The node to explain.
            
        
        Returns:
            A LogicalExpression representing the condition and the appropriate explanation.
        """
        if not node:
            return self.implies()
        condition_result = self.forward_evaluation(self.condition, node)

        skip_condition_statement = self.skip_condition_statement or (condition_result==True and self.skip_condition_statement_if_true) or (condition_result==False and self.skip_condition_statement_if_false)

        if condition_result:
            if skip_condition_statement:
                explanation = self.forward_explanation(self.explanation_if_true, node, no_increment=True)
            else:
                explanations = self.forward_multiple_explanations(
                        (self.condition, node),
                        (self.explanation_if_true, node),
                        no_increment = True
                    )
                explanation = And(*explanations)
        else:
            if skip_condition_statement:
                explanation = self.forward_explanation(self.explanation_if_false, node, no_increment=True)
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

class RecursivePossession(Explanation):
    """
    Represents an explanation provided by referring to the fact that
    the object referred to by a given pointer adjective possess a given pointer adjective,
    and this same pointer adjective refers to an object, which will possess the same given adjective,
    recursively continuing until a condition is met.

    e.g. RecursivePossession("next move", any_stop_conditions = [If("final move"), If("fully searched")])
    """
    max_recursion_depth = 5
    
    def __init__(self, *args, any_stop_conditions: list[If], explain_further=False, forward_pointers_explanations=True): #(pointer_adjective_name: str = None, adjective_name: str = None):
        super().__init__()
        """
        Initialize the RecursivePossession explanation.

        Usage:
            RecursivePossession(pointer_adjective_name, any_stop_conditions=[If(adjective)])
            RecursivePossession(start_pointer_adjective_name, pointer_adjective_name, any_stop_conditions=[If(adjective)])
        
        Args:
            *args: Either one or two string arguments.
                   If one argument: pointer_adjective_name
                   If two arguments: start_pointer_adjective_name, pointer_adjective_name

            start_pointer_adjective_name: The name of the pointer adjective that selects the object from which to start.
                                        If not given, the node itself will be checked.
            pointer_adjective_name: The name of the adjective to explain for the selected object.

        Keyword argument:
            any_stop_conditions (list) (required): The conditions to stop the recursion. Any of them will stop it.
            explain_further (bool): Wether to explain the Possession or just give the consequent without antecedent.
            forward_pointers_explanations (bool): whether it is necessary to explain why the node has the given pointer adjectives attached.
        """
        
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
        self.forward_pointers_explanations = forward_pointers_explanations

        for condition in any_stop_conditions:
            condition.forward_pointers_explanations = False

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

            if not self.forward_pointers_explanations:
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
                    explain_further=self.explain_further
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