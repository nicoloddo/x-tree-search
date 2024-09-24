from .base import Explanation

from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And

from typing import Any

class Assumption(Explanation):
    """Represents an explanation based on an assumption."""
    
    def __init__(self, description: str = None, *, implicit = False, necessary = False):
        """
        Args:
            description (str, optional): A textual description of the assumption.
            implicit (bool, optional): Indicates if the assumption is implicit. Defaults to False.
            necessary (bool, optional): Indicates if the assumption is necessary. Defaults to False.
        """
        super().__init__()
        self.description = description
        self.implicit_bool = implicit
        self.necessary_bool = necessary
    
    def build_description(self):
        """Constructs a description for the assumption if not provided."""
        return
    
    @property
    def verbose(self):
        """
        Provides a verbose description of the assumption.

        Returns:
            Postulate: A postulate object containing the verbose description.
        """
        if self.description is not None:
            verbose_string = "(assumption) " + self.description
        else:
            verbose_string = "(assumption) " + self.build_description()

        return Postulate(verbose_string)
    
    @property
    def minimal(self):
        """
        Provides a minimal description of the assumption.

        Returns:
            Postulate: A postulate object containing the minimal description.
        """
        return Postulate("(from assumptions)")

    def _explain(self, node: Any) -> LogicalExpression:
        """
        Generates a logical expression based on the assumption's properties.

        Args:
            node (Any): The node to which the assumption applies.

        Returns:
            LogicalExpression: The logical expression representing the assumption, or None if not applicable.
        """
        self.refer_to_nodes_as = self.framework.refer_to_nodes_as

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
                raise ValueError("Invalid assumptions verbosity setting.")

class PossessionAssumption(Assumption):
    """Represents the assumption underlying a possession adjective attribution.
    
    Example:
        "Definition of 'score' is node.score"
    """
    
    def __init__(self, adjective_name: str, definition: str = None):
        """
        Args:
            adjective_name (str): The name of the boolean adjective.
            definition (str, optional): The definition of the adjective. Defaults to None.
        """
        self.adjective_name = adjective_name
        self.definition = definition
        super().__init__(implicit=True)

    def build_description(self):
        """
        Constructs a description for the possession assumption.

        Returns:
            str: The constructed description.
        """
        if self.definition is not None:
            return f"Definition of \"{self.adjective_name}\" is {self.definition}"
        else:
            return f"Definition of \"{self.adjective_name}\""

class ComparisonAssumption(Assumption):
    """Represents the assumption underlying the comparison between two nodes.
    
    Example:
        "By definition, node1 is 'taller' than node2 if node1 height > node2 height."
    """
    
    def __init__(self, comparison_adjective_name: str, pointer_adjective_name: str, operator: str):
        """
        Args:
            comparison_adjective_name (str): The name of the comparison adjective.
            pointer_adjective_name (str): The name of the pointer adjective used for comparison.
            operator (str): The comparison operator.
        """
        self.comparison_adjective_name = comparison_adjective_name
        self.pointer_adjective_name = pointer_adjective_name
        self.operator = operator
        super().__init__(implicit=True)
    
    def build_description(self):
        """
        Constructs a description for the comparison assumption.

        Returns:
            str: The constructed description.
        """
        return f"By definition, {self.refer_to_nodes_as}1 is \"{self.comparison_adjective_name}\" than {self.refer_to_nodes_as}2 if {self.refer_to_nodes_as}1 {self.pointer_adjective_name} {self.operator} {self.refer_to_nodes_as}2 {self.pointer_adjective_name}"

class RankAssumption(Assumption):
    """Represents the assumption underlying the ranking of nodes.
    
    Example:
        "By definition a node is 'highest' if it's 'altitude' is higher than all 'mountain' group."
    """
    
    def __init__(self, rank_type: str, name: str, comparison_adjective_name: str, group_pointer_adjective_name: str):
        """
        Args:
            rank_type (str): The type of ranking (supported: max, min).
            name (str): The name of the rank.
            comparison_adjective_name (str): The name of the comparison adjective.
            group_pointer_adjective_name (str): The name of the group pointer adjective among which we are ranking the node.
        """
        self.rank_type = rank_type
        self.name = name
        self.comparison_adjective_name = comparison_adjective_name
        self.group_pointer_adjective_name = group_pointer_adjective_name
        super().__init__(implicit=True)
    
    def build_description(self):
        """
        Constructs a description for the rank assumption.

        Returns:
            str: The constructed description.
        """
        if self.rank_type == 'max':
            return f"By definition a {self.refer_to_nodes_as} is \"{self.name}\" if it's \"{self.comparison_adjective_name}\" than all \"{self.group_pointer_adjective_name}\""
        elif self.rank_type == 'min':
            return f"By definition a {self.refer_to_nodes_as} is \"{self.name}\" if it's not \"{self.comparison_adjective_name}\" than all \"{self.group_pointer_adjective_name}\""
        else:
            raise ValueError("RankAssumption of unknown type.")