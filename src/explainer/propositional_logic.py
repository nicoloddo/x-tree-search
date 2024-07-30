from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
import textwrap

class LogicalExpression(ABC):
    """Abstract base class for all logical expressions."""
    print_mode = 'logic'

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        """Evaluate the logical expression given an interpretation."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the logical expression."""
        pass

class Postulate(LogicalExpression):
    """Represents an undefeasible fact."""
    def __init__(self, expr):
        self.expr = expr
    
    def __str__(self) -> str:
        return self.expr
    
class Proposition(LogicalExpression):
    """Represents a basic proposition in propositional logic."""

    def __init__(self, obj_name, expr: str, evaluation: Any = None):
        self.obj_name = obj_name
        self.expr = expr
        
        if evaluation is None:
            self.evaluation = '?'
        elif type(evaluation) is list:
            self.evaluation = ', '.join([str(val) for val in evaluation])
        else:
            self.evaluation = evaluation
    
    def add_tag(self, tag: str):
        self.tag = tag

    def __str__(self) -> str:
        if isinstance(self.evaluation, bool):
            if self.evaluation:
                string_end = f"is {self.expr}"
            else:
                if self.print_mode == 'logic':
                    negation = f"¬({self.expr})"
                elif self.print_mode == 'verbal':
                    negation = f"not {self.expr}"

                string_end = f"is {negation}"
        else:
            if self.print_mode == 'logic':
                string_end = f"has {self.expr} = {self.evaluation}"
            elif self.print_mode == 'verbal':
                string_end = f"has as {self.expr} {self.evaluation}"

        to_string = f"{self.obj_name} {string_end}"

        if hasattr(self, "tag"):
            to_string += f" ({self.tag})"
        return to_string
    
class UnaryOperator(LogicalExpression):
    def __new__(cls, expr: LogicalExpression):
        if not expr:
            return None
        return super(UnaryOperator, cls).__new__(cls)

    def __init__(self, expr: LogicalExpression):
        self.expr = expr

class NAryOperator(LogicalExpression):
    symbol = 'undefined symbol'

    def __new__(cls, *exprs: LogicalExpression):
        filtered_exprs = tuple(filter(None, exprs)) # filter None expressions
        if not filtered_exprs:
            return None
        instance = super(NAryOperator, cls).__new__(cls)
        instance.exprs = filtered_exprs
        return instance
    
    def __init__(self, *exprs: LogicalExpression):
        pass # we set the exprs in the __new__ after filtering

    def __str__(self) -> str:
        if self.print_mode == 'logic':
            operator_string = self.symbol
        elif self.print_mode == 'verbal':
            operator_string = self.verbal

        if len(self.exprs) > 2 or not all(isinstance(expr, Proposition) for expr in self.exprs):
            joining_string = '\n' + operator_string + ' '
        else:
            joining_string = ' ' + operator_string + ' '
        
        joined = joining_string.join(str(expr) for expr in self.exprs)
        return joined

class And(NAryOperator):
    """Represents the conjunction of logical expressions."""
    symbol = '∧'
    verbal = 'and'

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return all(expr.evaluate(interpretation) for expr in self.exprs)

class Or(NAryOperator):
    """Represents the disjunction of logical expressions."""
    symbol = '||'
    verbal = 'or'

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return any(expr.evaluate(interpretation) for expr in self.exprs if expr is not None)

class Implies(LogicalExpression):
    """Represents the implication between two logical expressions."""
    symbol = '←'
    verbal = 'because'

    def __init__(self, antecedent: LogicalExpression, consequent: LogicalExpression):
        self.antecedent = antecedent
        self.consequent = consequent

        self._str_settings_list = {}

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return (not self.antecedent.evaluate(interpretation)) or self.consequent.evaluate(interpretation)

    def _str_settings(self, **kwargs):
        for key, value in kwargs.items():
            self._str_settings_list[key] = value

    def __str__(self) -> str:

        if self.print_mode == 'logic':
            operator_string = self.symbol
        elif self.print_mode == 'verbal':
            operator_string = self.verbal

        operator_string = operator_string + '\n'

        if "first_print" in self._str_settings_list:
            symbol = operator_string + '\n'
        else:
            symbol = operator_string

        if hasattr(self.antecedent, "current_explanation_depth"):
            depth = self.antecedent.current_explanation_depth
            indentation = '\t' * depth

            if "print_depth" in self._str_settings_list:
                self.antecedent = f"Depth {depth}:\n{self.antecedent}"

            self.antecedent = textwrap.indent(f"{self.antecedent}", indentation)
          
        return f"{self.consequent} {symbol} {self.antecedent}"