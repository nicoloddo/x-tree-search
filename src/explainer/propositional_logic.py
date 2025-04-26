from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
import textwrap
import inspect


class LogicalExpression(ABC):
    """Abstract base class for all logical expressions."""

    print_mode = "logic"
    hyperlink_mode = False
    tree_node_cls = None

    def __init__(self):
        self.nullified = False  # Disable the expression like this

        self.subject = None
        self.predicate = None
        self.evaluation = None

        self.record = None

        # Aux for tactics go here
        self.compacted = False

    @classmethod
    def format_node(cls, node):
        return (
            f"::node::({node.id})[{node.game_tree_node_string}]"
            if cls.hyperlink_mode
            else str(node)
        )

    @classmethod
    def set_hyperlink_mode(cls, value: bool, tree_node_cls=None) -> bool:
        if value == True:
            if not tree_node_cls:
                raise SyntaxError(
                    "To set the hyperlink_mode to True, you need to pass a tree_node_cls for validation purposes."
                )

            # Get all attributes and methods, including properties
            class_attrs = set(dir(tree_node_cls))

            # Get attributes defined in __init__
            try:
                init_source = inspect.getsource(tree_node_cls.__init__)
                init_attrs = {
                    line.split("self.")[1].split("=")[0].strip()
                    for line in init_source.split("\n")
                    if "self." in line and "=" in line
                }
            except:
                init_attrs = set()

            # Combine both sets of attributes
            all_attrs = class_attrs | init_attrs

            required_attrs = {"id", "game_state", "game_tree_node_string"}
            missing_attrs = required_attrs - all_attrs

            if missing_attrs:
                for attr in missing_attrs:
                    print(
                        f"To use hyperlink mode, the nodes of your search algorithm must have a '{attr}' attribute. The class {tree_node_cls} does not have it. It has:\n{class_attrs}"
                    )
                return False
            else:
                cls.hyperlink_mode = True
                cls.tree_node_cls = tree_node_cls
                return True  # activated
        else:
            cls.hyperlink_mode = False
            return False  # not activated

    def __str__(self) -> str:
        if self.nullified:
            return None
        else:
            return self._to_str()

    @abstractmethod
    def _to_str(self) -> str:
        """Return a string representation of the logical expression."""
        pass

    def set_record(self, record):
        if self.record is None:
            self.record = record

    def update_record(self, record):
        if self.record is not None:
            self.record.update(record)

    def nullify(self):
        self.nullified = True


class Postulate(LogicalExpression):
    """Represents an undefeasible fact."""

    def __init__(self, predicate):
        super().__init__()
        self.predicate = predicate

    def _to_str(self) -> str:
        return self.predicate


class Proposition(LogicalExpression):
    """Represents a basic proposition in propositional logic."""

    to_be = {"singular": "is", "plural": "are"}
    to_have = {"singular": "has", "plural": "have"}

    def __init__(self, subject, predicate: str, evaluation: Any = None, object=None):
        super().__init__()
        self.subject = subject
        self.predicate = predicate
        self.evaluation = evaluation
        self.object = (
            object  # Used for comparison predicates: e.g. node is better than what?
        )

    def add_info(self, additional_info: str):
        # Function to add possible other info
        self.additional_info = additional_info

    def _to_str(self) -> str:
        self.build_str_components()
        to_string = f"{self.subject_str} {self.verb_str} {self.predicate_str}{self.evaluation_str}{self.object_str}"
        if hasattr(self, "additional_info"):
            to_string += f" ({self.additional_info})"
        return to_string

    def build_str_components(self) -> None:

        verb_number = (
            "singular"
            if self.subject is None or not isinstance(self.subject, list)
            else "plural"
        )

        if self.subject is None:
            subject = "::node::(None)[]" if self.hyperlink_mode else "?"
        elif self.tree_node_cls is not None and isinstance(
            self.subject, self.tree_node_cls
        ):
            subject = self.format_node(self.subject)
        elif isinstance(self.subject, list):
            subject = ", ".join(
                (
                    self.format_node(item)
                    if self.tree_node_cls is not None
                    and isinstance(item, self.tree_node_cls)
                    else str(item)
                )
                for item in self.subject
            )
        else:
            subject = self.subject

        if self.object is None:
            object = ""
        elif self.tree_node_cls is not None and isinstance(
            self.object, self.tree_node_cls
        ):
            object = " " + self.format_node(self.object)
        elif isinstance(self.object, list):
            object = " " + ", ".join(
                (
                    self.format_node(item)
                    if self.tree_node_cls is not None
                    and isinstance(item, self.tree_node_cls)
                    else str(item)
                )
                for item in self.object
            )
        else:
            object = " " + self.object

        predicate = self.predicate

        verb_type = self.to_be if isinstance(self.evaluation, bool) else self.to_have
        verb = verb_type[verb_number]

        if self.evaluation is None:
            evaluation = "?"
        elif self.tree_node_cls is not None and isinstance(
            self.evaluation, self.tree_node_cls
        ):
            evaluation = self.format_node(self.evaluation)
        elif isinstance(self.evaluation, list):
            evaluation = ", ".join(
                (
                    self.format_node(item)
                    if self.tree_node_cls is not None
                    and isinstance(item, self.tree_node_cls)
                    else str(item)
                )
                for item in self.evaluation
            )
        else:
            evaluation = self.evaluation

        if isinstance(self.evaluation, bool):
            evaluation = ""
            if self.evaluation:
                pass
            else:
                if self.print_mode == "logic":
                    negation = f"¬({predicate})"
                elif self.print_mode == "verbal":
                    negation = f"not {predicate}"
                predicate = negation
        else:
            if self.print_mode == "logic":
                evaluation = f"= {evaluation}"
            elif self.print_mode == "verbal":
                evaluation = f" {evaluation}"

        self.subject_str = subject
        self.verb_str = verb
        self.predicate_str = predicate
        self.evaluation_str = evaluation
        self.object_str = object


class Implies(LogicalExpression):
    """Represents the implication between two logical expressions."""

    symbol = "←"
    verbal = "because"

    def __init__(self, antecedent: LogicalExpression, consequent: LogicalExpression):
        super().__init__()
        self.antecedent = antecedent
        self.consequent = consequent
        self._str_settings_list = {}

    def add_info(self, additional_info: str):
        # Function to add possible other info
        self.consequent.additional_info = additional_info

    # Property for subject
    @property
    def subject(self):
        return self.consequent.subject

    @subject.setter
    def subject(self, value):
        if hasattr(self, "consequent"):
            self.consequent.subject = value

    # Property for predicate
    @property
    def predicate(self):
        return self.consequent.predicate

    @predicate.setter
    def predicate(self, value):
        if hasattr(self, "consequent"):
            self.consequent.predicate = value

    # Property for evaluation
    @property
    def evaluation(self):
        return self.consequent.evaluation

    @evaluation.setter
    def evaluation(self, value):
        if hasattr(self, "consequent"):
            self.consequent.evaluation = value

    def _str_settings(self, **kwargs):
        for key, value in kwargs.items():
            self._str_settings_list[key] = value

    def set_record(self, record):
        self.antecedent.set_record(record)
        self.consequent.set_record(record)
        super().set_record(record)

    def _to_str(self) -> str:
        if self.antecedent is None:
            return str(self.consequent)
        elif self.consequent is None:
            return str(self.antecedent)

        if self.print_mode == "logic":
            operator_string = self.symbol
        elif self.print_mode == "verbal":
            operator_string = self.verbal

        if "first_print" in self._str_settings_list:
            symbol = operator_string + "\n"
        else:
            symbol = operator_string

        if hasattr(self.antecedent, "current_explanation_depth"):
            depth = self.antecedent.current_explanation_depth
            indentation = "\t" * depth

            if "print_depth" in self._str_settings_list:
                antecedent_str = f"Depth {depth}:\n{self.antecedent}"
            else:
                antecedent_str = str(self.antecedent)

            antecedent_str = textwrap.indent(antecedent_str, indentation)
        else:
            raise ValueError(
                f"There is no found antecedent for the following consequent:\n{self.consequent}"
            )

        if self.print_mode == "logic":
            to_string = f"{self.consequent} {symbol}\n {antecedent_str}"
        elif self.print_mode == "verbal":
            to_string = f"{self.consequent} ({symbol}\n {antecedent_str})"

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
    symbol = "undefined symbol"

    def is_valid_expr(expr):
        return expr is not None and not getattr(expr, "nullified", False)

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

    def _to_str(self) -> str:
        filtered_exprs = tuple(filter(NAryOperator.is_valid_expr, self.exprs))
        if not filtered_exprs:
            return None
        if len(filtered_exprs) == 1:
            return str(filtered_exprs[0])

        if self.print_mode == "logic":
            operator_string = self.symbol
        elif self.print_mode == "verbal":
            operator_string = self.verbal

        if len(filtered_exprs) > 2 or not all(
            isinstance(expr, Proposition) for expr in filtered_exprs
        ):
            joining_string = "\n" + operator_string + " "
        else:
            # They are only two propositions to tie
            joining_string = "\n" + operator_string + " "

        joined = joining_string.join(str(expr) for expr in filtered_exprs)
        return joined

    def get_flat_exprs(
        self, operator=None, *, min_depth=0, max_depth=float("inf"), current_depth=0
    ):
        """Returns exprs contained in following exprs's NAryOperators between min depth and max depth, flattened."""
        if operator is None:
            operator = self

        if current_depth >= max_depth or not isinstance(operator, NAryOperator):
            if current_depth >= min_depth:
                return [operator]
            else:
                return []  # Don't add elements if we are under the min depth

        flattened = []
        for expr in operator.exprs:
            flattened.extend(
                self.get_flat_exprs(
                    expr,
                    min_depth=min_depth,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                )
            )
        return flattened


class And(NAryOperator):
    """Represents the conjunction of logical expressions."""

    symbol = "∧"
    verbal = "and"


class Or(NAryOperator):
    """Represents the disjunction of logical expressions."""

    symbol = "||"
    verbal = "or"
