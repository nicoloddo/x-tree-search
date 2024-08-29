from .base import Explanation

from src.explainer.propositional_logic import LogicalExpression, Postulate, Proposition, And

from typing import Any

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