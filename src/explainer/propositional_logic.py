from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
import textwrap

class LogicalExpression(ABC):
    """Abstract base class for all logical expressions."""
    print_mode = 'logic'

    def __init__(self):
        self.record = None
        self.subject = None
        self.predicate = None
        self.evaluation = None

        self.nullified = False
    
    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the logical expression."""
        pass

    def set_record(self, record):
        if self.record is None:
            self.record = record
    
    def update_record(self, record):
        if self.record is not None:
            self.record.update = record

    def nullify(self):
        self.nullified = True

class Postulate(LogicalExpression):
    """Represents an undefeasible fact."""
    def __init__(self, predicate):
        super().__init__()
        self.predicate = predicate
    
    def __str__(self) -> str:
        return self.predicate
    
class Proposition(LogicalExpression):
    """Represents a basic proposition in propositional logic."""
    to_be = {'singular': 'is', 'plural': 'are'}
    to_have = {'singular': 'has', 'plural': 'have'}

    def __init__(self, subject, predicate: str, evaluation: Any = None, object = None):
        super().__init__()
        self.subject = subject
        self.predicate = predicate
        self.object = object
        
        self.evaluation = evaluation
    
    def add_tag(self, tag: str):
        self.tag = tag

    def __str__(self) -> str:
        if self.evaluation is None:
            self.evaluation = '?'
        elif type(self.evaluation) is list:
            self.evaluation = ', '.join([str(val) for val in self.evaluation])
        
        if self.subject is None:
            self.subject = '?'
            predicate_type = 'singular'
        elif type(self.subject) is list:
            self.subject = ', '.join([str(val) for val in self.subject])
            predicate_type = 'plural'
        else:
            predicate_type = 'singular'

        if self.object is not None:
            if type(self.object) is list:
                object_str = ', '.join([str(val) for val in self.object])
            else:
                object_str = self.object
            expression = f"{self.predicate} {object_str}"
        else:
            expression = self.predicate

        if isinstance(self.evaluation, bool):
            predicate = self.to_be[predicate_type]

            if self.evaluation:
                string_end = f"{predicate} {expression}"
            else:
                if self.print_mode == 'logic':
                    negation = f"¬({expression})"
                elif self.print_mode == 'verbal':
                    negation = f"not {expression}"

                string_end = f"{predicate} {negation}"
        else:
            predicate = self.to_have[predicate_type]
            if self.print_mode == 'logic':
                string_end = f"{predicate} {expression} = {self.evaluation}"
            elif self.print_mode == 'verbal':
                string_end = f"{predicate} {expression} {self.evaluation}"

        to_string = f"{self.subject} {string_end}"

        if hasattr(self, "tag"):
            to_string += f" ({self.tag})"
        return to_string

class Implies(LogicalExpression):
    """Represents the implication between two logical expressions."""
    symbol = '←'
    verbal = 'because'

    def __init__(self, antecedent: LogicalExpression, consequent: LogicalExpression):
        super().__init__()
        self.antecedent = antecedent
        self.consequent = consequent

        self.predicate = consequent.predicate
        self.subject = consequent.subject
        self.evaluation = consequent.evaluation

        self._str_settings_list = {}

    def _str_settings(self, **kwargs):
        for key, value in kwargs.items():
            self._str_settings_list[key] = value
    
    def set_record(self, record):
        self.antecedent.set_record(record)
        self.consequent.set_record(record)
        super().set_record(record)

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
    
class UnaryOperator(LogicalExpression):
    def __new__(cls, predicate: LogicalExpression):
        if not predicate:
            return None
        return super(UnaryOperator, cls).__new__(cls)

    def __init__(self, predicate: LogicalExpression):
        super().__init__()
        self.predicate = predicate

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
        # Do here init operations
        instance.__newinit__(filtered_exprs)
        return instance
    
    def __newinit__(self, filtered_exprs):
        self.exprs = filtered_exprs
        super().__init__()

    def __init__(self, *exprs: LogicalExpression):
        # Do not modify this method, use the newinit instead
        pass

    def set_record(self, record):
        for expr in self.exprs:
            expr.set_record(record)
        super().set_record(record)

    def update_record(self, record):
        for expr in self.exprs:
            expr.update_record(record)
        super().update_record(record)

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
    
    def get_flat_exprs(self, operator=None, *, max_depth=float('inf'), current_depth=0):
        if operator is None:
            operator = self

        if current_depth >= max_depth or not isinstance(operator, NAryOperator):
            return [operator]
        
        flattened = []
        for expr in operator.exprs:
            flattened.extend(self.get_flat_exprs(expr, max_depth=max_depth, current_depth=current_depth + 1))
        return flattened

class And(NAryOperator):
    """Represents the conjunction of logical expressions."""
    symbol = '∧'
    verbal = 'and'

class Or(NAryOperator):
    """Represents the disjunction of logical expressions."""
    symbol = '||'
    verbal = 'or'