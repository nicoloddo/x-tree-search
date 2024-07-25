from abc import ABC, abstractmethod
from typing import List, Union, Dict

class LogicalExpression(ABC):
    """Abstract base class for all logical expressions."""

    @abstractmethod
    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        """Evaluate the logical expression given an interpretation."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the logical expression."""
        pass

class Proposition(LogicalExpression):
    """Represents a basic proposition in propositional logic."""

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return interpretation.get(self.name, False)

    def __str__(self) -> str:
        return self.name
    
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
        if len(self.exprs) > 2 or not all(isinstance(expr, Proposition) for expr in self.exprs):
            joining_string = '\n ' + self.symbol + ' '
        else:
            joining_string = ' ' + self.symbol + ' '
        
        joined = joining_string.join(str(expr) for expr in self.exprs)
        return joined

class Not(UnaryOperator):
    """Represents the negation of a logical expression."""

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return not self.expr.evaluate(interpretation)

    def __str__(self) -> str:
        return f"¬({self.expr})"

class And(NAryOperator):
    """Represents the conjunction of logical expressions."""
    symbol = '∧'

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return all(expr.evaluate(interpretation) for expr in self.exprs)

class Or(NAryOperator):
    """Represents the disjunction of logical expressions."""
    symbol = '||'

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return any(expr.evaluate(interpretation) for expr in self.exprs if expr is not None)

class Implies(LogicalExpression):
    """Represents the implication between two logical expressions."""

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
        if "first_print" in self._str_settings_list:
            symbol = '←\n'
        else:
            symbol = '←'

        if "explanation_depth" in self._str_settings_list and "print_depth" in self._str_settings_list:
            depth = self._str_settings_list["explanation_depth"]
            return f"Depth {depth}: [{self.consequent} {symbol} {self.antecedent}]"
        else:
            return f"[{self.consequent} {symbol} {self.antecedent}]"
        

class Iff(LogicalExpression):
    """Represents the biconditional (if and only if) between two logical expressions."""

    def __init__(self, left: LogicalExpression, right: LogicalExpression):
        self.left = left
        self.right = right

    def evaluate(self, interpretation: Dict[str, bool]) -> bool:
        return self.left.evaluate(interpretation) == self.right.evaluate(interpretation)

    def __str__(self) -> str:
        return f"({self.left} ↔ {self.right})"

def simplify(expr: LogicalExpression) -> LogicalExpression:
    """
    Simplify a logical expression using basic logical equivalences.
    This is a basic implementation and doesn't cover all possible simplifications.
    """
    if isinstance(expr, (Proposition, Not)):
        return expr
    elif isinstance(expr, And):
        simplified = [simplify(e) for e in expr.exprs]
        simplified = [e for e in simplified if not (isinstance(e, And) and len(e.exprs) == 0)]
        if len(simplified) == 0:
            return Proposition("True")
        elif len(simplified) == 1:
            return simplified[0]
        else:
            return And(*simplified)
    elif isinstance(expr, Or):
        simplified = [simplify(e) for e in expr.exprs]
        simplified = [e for e in simplified if not (isinstance(e, Or) and len(e.exprs) == 0)]
        if len(simplified) == 0:
            return Proposition("False")
        elif len(simplified) == 1:
            return simplified[0]
        else:
            return Or(*simplified)
    elif isinstance(expr, Implies):
        return Implies(simplify(expr.antecedent), simplify(expr.consequent))
    elif isinstance(expr, Iff):
        return Iff(simplify(expr.left), simplify(expr.right))
    else:
        return expr

# Example usage
def main():
    p = Proposition("p")
    q = Proposition("q")
    r = Proposition("r")

    # Example: (p ∧ q) → (p ∨ r)
    complex_expr = Implies(And(p, q), Or(p, r))
    print(f"Complex expression: {complex_expr}")

    # Evaluate the expression
    interpretation = {"p": True, "q": False, "r": True}
    result = complex_expr.evaluate(interpretation)
    print(f"Evaluation result: {result}")

    # Simplify an expression
    simplified = simplify(And(p, Or(q, And(r, Not(r)))))
    print(f"Simplified expression: {simplified}")

if __name__ == "__main__":
    main()