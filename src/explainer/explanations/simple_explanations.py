from .base import Explanation

from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And

from typing import Any

""" Assumptions """
class Assumption(Explanation):
    """Represents an explanation based on an assumption."""    
    def __init__(self, description: str = None, *, implicit = False, necessary = False):
        super().__init__()
        """
        Initialize the Assumption.
        
        Args:
            description: A string describing the assumption.
        """

        self.description = description
        self.implicit_bool = implicit
        self.necessary_bool = necessary
    
    def build_description():
        return
    
    @property
    def verbose(self):
        if self.description is not None:
            verbose_string = "(assumption) " + self.description
        else:
            verbose_string = "(assumption) " + self.build_description()

        return Postulate(verbose_string)
    
    @property
    def minimal(self):
        return Postulate("(from assumptions)")

    def _explain(self, node: Any) -> LogicalExpression:
        self.refer_to_nodes_as = self.framework.refer_to_nodes_as

        """Return the assumption as a Proposition."""
        if self.necessary_bool:
            return self.verbose
        
        else:
            if not self.framework.settings.print_implicit_assumptions:
                if self.implicit_bool:
                    return None
                
            if self.framework.settings.assumptions_verbosity == 'verbose':
                return self.verbose

            elif self.framework.settings.assumptions_verbosity == 'minimal':
                return self.minimal

            elif self.framework.settings.assumptions_verbosity == 'no':
                return None
            
            elif self.framework.settings.assumptions_verbosity == 'if_asked':
                if self.current_explanation_depth == 1:
                    return self.verbose
                else:
                    return None

            else:
                raise ValueError("Framework has unvalid assumptions verbosity.")
    
    def implies(self) -> LogicalExpression:
        """Return the assumption as a Proposition."""
        return self.verbose

class PossessionAssumption(Assumption):
    """Represents the assumption underlying a boolean adjective attribution."""
    
    def __init__(self, adjective_name: str, definition: str = None):
        """
        Initialize the ComparisonAssumption.
        
        Args:
            adjective_name: The name of the boolean adjective.
        """
        self.adjective_name = adjective_name
        self.definition = definition
        super().__init__(implicit = True)

    def build_description(self):
        if self.definition is not None:
            return f"Definition of \"{self.adjective_name}\" is {self.definition}"
        else:
            return f"Definition of \"{self.adjective_name}\""

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
        self.comparison_adjective_name = comparison_adjective_name
        self.pointer_adjective_name = pointer_adjective_name
        self.operator = operator
        super().__init__(implicit = True)
    
    def build_description(self):
        return f"By definition, {self.refer_to_nodes_as}1 is \"{self.comparison_adjective_name}\" than {self.refer_to_nodes_as}2 if {self.refer_to_nodes_as}1 {self.pointer_adjective_name} {self.operator} {self.refer_to_nodes_as}2 {self.pointer_adjective_name}"

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
        self.rank_type = rank_type
        self.name = name
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name

        super().__init__(implicit = True)
    
    def build_description(self):
        if self.rank_type == 'max':
            return f"By definition a {self.refer_to_nodes_as} is \"{self.name}\" if it's \"{self.comparison_adjective_name}\" than all \"{self.group_pointer_adjective_name}\""
        elif self.rank_type == 'min':
            return f"By definition a {self.refer_to_nodes_as} is \"{self.name}\" if it's not \"{self.comparison_adjective_name}\" than all \"{self.group_pointer_adjective_name}\""
        else:
            raise ValueError("RankAssumption of unknown type.")

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
            raise ValueError("A Possession explanation takes a max of 2 arguments")

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
            explanation = self.forward_explanation(adjective, node) # Why the node has this property?

        else:
            pointer_adjective = self.framework.get_adjective(self.pointer_adjective_name)
            referred_object = self.forward_evaluation(pointer_adjective, node)

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
        
class Comparison(Explanation):
    """Represents an explanation given by referring to 
    a comparison between a node and another."""

    def __init__(self, *args, forward_property_explanations = False): #(obj1_pointer_adjective_name: str, comparison_adjective_name: str, obj2_pointer_adjective_name: str)
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

            keyword argument:
            forward_property_explanations: whether it is necessary to explain why the node has the given pointer adjectives attached.
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
        
        self.forward_property_explanations = forward_property_explanations

    def _explain(self, node: Any):
        comparison_adjective = self.framework.get_adjective(self.comparison_adjective_name)
        
        obj2_pointer_adjective = self.framework.get_adjective(self.obj2_pointer_adjective_name)
        obj2 = self.forward_evaluation(obj2_pointer_adjective, node)

        if self.obj1_pointer_adjective_name is None:
            if self.forward_property_explanations:
                explanations = self.forward_multiple_explanations(
                        (comparison_adjective, node, obj2), # why obj1 is <(e.g.) better> than obj2?
                        (obj2_pointer_adjective, node) # why the node has this pointer adjective?
                    )
                explanation = And(*explanations)
            else:
                explanation = self.forward_explanation(comparison_adjective, node, obj2)
            
        else:
            obj1_pointer_adjective = self.framework.get_adjective(self.obj1_pointer_adjective_name)
            obj1 = self.forward_evaluation(obj1_pointer_adjective, node)

            if self.forward_property_explanations:
                explanations = self.forward_multiple_explanations(
                        (comparison_adjective, obj1, obj2), # why obj1 is <(e.g.) better> than obj2?
                        (obj1_pointer_adjective, node), # why the node has this pointer adjective?
                        (obj2_pointer_adjective, node) # why the node has this pointer adjective?
                    )
                explanation = And(*explanations)
            else:
                explanation = self.forward_explanation(comparison_adjective, obj1, obj2)

        return explanation
    
    def implies(self) -> LogicalExpression:
        """ Generates a proposition that contitutes the antecedent of an
        implication explaining why a certain object referenced through a pointer adjectiv
        is <(e.g.) better> than another."""
        # TODO: do the implies
        if self.obj1_pointer_adjective_name is None:
            obj1_string = "Node"
        else:
            obj1_string = self.obj1_pointer_adjective_name

        return Postulate(f"{obj1_string} is {self.comparison_adjective_name} than {self.obj1_pointer_adjective_name}")

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
        group = self.forward_evaluation(group_pointer_adjective, node)

        to_forward_explanations = [(comparison_adjective, node, other_node) for other_node in group]
        to_forward_explanations.append((group_pointer_adjective, node))
        explanations = self.forward_multiple_explanations(*to_forward_explanations)
        base_explanation = explanations.pop() # pop the group_pointer_adjective explanation
                
        explanation = And(base_explanation, And(*explanations))
        return explanation

    def implies(self) -> LogicalExpression:
        is_what = self.comparison_adjective_name if self.positive_implication else f"not {self.comparison_adjective_name}"
        return Postulate(f"Node {is_what} than all nodes in {self.group_pointer_adjective_name}")

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

    def _contextualize(self):
        for exp in self.explanations:
            exp.contextualize(self.explanation_of_adjective)

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