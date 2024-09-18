from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
import textwrap

class LogicalExpression(ABC):
    """Abstract base class for all logical expressions."""
    print_mode = 'logic'
    
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
    to_be = {'singular': 'is', 'plural': 'are'}
    to_have = {'singular': 'has', 'plural': 'have'}

    def __init__(self, obj_name, expr: str, evaluation: Any = None):
        self.obj_name = obj_name
        self.expr = expr
        
        self.evaluation = evaluation

        self.nullified = False

    def nullify(self):
        self.nullified = True
    
    def add_tag(self, tag: str):
        self.tag = tag

    def __str__(self) -> str:
        if self.evaluation is None:
            self.evaluation = '?'
        elif type(self.evaluation) is list:
            self.evaluation = ', '.join([str(val) for val in self.evaluation])
        
        if self.obj_name is None:
            self.obj_name = '?'
            predicate_type = 'singular'
        elif type(self.obj_name) is list:
            self.obj_name = ', '.join([str(val) for val in self.obj_name])
            predicate_type = 'plural'
        else:
            predicate_type = 'singular'

        if isinstance(self.evaluation, bool):
            predicate = self.to_be[predicate_type]

            if self.evaluation:
                string_end = f"{predicate} {self.expr}"
            else:
                if self.print_mode == 'logic':
                    negation = f"¬({self.expr})"
                elif self.print_mode == 'verbal':
                    negation = f"not {self.expr}"

                string_end = f"{predicate} {negation}"
        else:
            predicate = self.to_have[predicate_type]
            if self.print_mode == 'logic':
                string_end = f"{predicate} {self.expr} = {self.evaluation}"
            elif self.print_mode == 'verbal':
                string_end = f"{predicate} {self.expr} {self.evaluation}"

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

    def is_valid_expr(expr):
        return expr is not None and not getattr(expr, 'nullified', False)
    
    def __new__(cls, *exprs: LogicalExpression):

        filtered_exprs = tuple(filter(NAryOperator.is_valid_expr, exprs))
        if not filtered_exprs:
            return None
        if len(filtered_exprs) == 1:
            return filtered_exprs[0]
        instance = super(NAryOperator, cls).__new__(cls)
        instance.exprs = filtered_exprs
        return instance
    
    def __init__(self, *exprs: LogicalExpression):
        pass # we set the exprs in the __new__ after filtering

    def __str__(self) -> str:
        filtered_exprs = tuple(filter(NAryOperator.is_valid_expr, self.exprs))
        if not filtered_exprs:
            return None
        if len(filtered_exprs) == 1:
            return str(filtered_exprs[0])

        if self.print_mode == 'logic':
            operator_string = self.symbol
        elif self.print_mode == 'verbal':
            operator_string = self.verbal

        if len(filtered_exprs) > 2 or not all(isinstance(expr, Proposition) for expr in filtered_exprs):
            joining_string = '\n' + operator_string + ' '
        else:
            # They are only two propositions to tie
            joining_string = '\n' + operator_string + ' '
        
        joined = joining_string.join(str(expr) for expr in filtered_exprs)
        return joined

class And(NAryOperator):
    """Represents the conjunction of logical expressions."""
    symbol = '∧'
    verbal = 'and'

class Or(NAryOperator):
    """Represents the disjunction of logical expressions."""
    symbol = '||'
    verbal = 'or'

class Implies(LogicalExpression):
    """Represents the implication between two logical expressions."""
    symbol = '←'
    verbal = 'because'

    def __init__(self, antecedent: LogicalExpression, consequent: LogicalExpression):
        self.antecedent = antecedent
        self.consequent = consequent

        self._str_settings_list = {}

    def _str_settings(self, **kwargs):
        for key, value in kwargs.items():
            self._str_settings_list[key] = value

    def __str__(self) -> str:

        if self.print_mode == 'logic':
            operator_string = self.symbol
        elif self.print_mode == 'verbal':
            operator_string = self.verbal

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

        if self.print_mode == 'logic':
            to_string = f"{self.consequent} {symbol}\n {self.antecedent}"
        elif self.print_mode == 'verbal':
            to_string = f"{self.consequent} ({symbol}\n {self.antecedent})"

        return to_string