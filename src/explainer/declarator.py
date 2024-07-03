import importlib
import inspect
import ast
from typing import Any, Dict, List, Set

from src.explainer.framework import ArgumentationFramework
from src.explainer.adjective import BooleanAdjective, PointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective
from src.explainer.explanation import Explanation, Possession, Assumption, PossessionCondition, ConditionalExplanation, CompositeExplanation


class MultiModuleTreeSearchDeclarator:
    def __init__(self, module_names: List[str]):
        self.modules = [importlib.import_module(name) for name in module_names]
        self.framework = ArgumentationFramework()
        self.node_classes = self._find_node_classes()

    def declare_algorithm(self):
        """Declare the algorithm using the Argumentation Framework."""
        self._add_adjectives()
        self._add_comparison_adjectives()
        self._analyze_code_for_explanations()
        
        tree_search_functions = self._find_tree_search_function()
        for func in tree_search_functions:
            self._analyze_tree_search_function(func)
        
        return self.framework
    
    def _find_node_classes(self) -> List[type]:
        """Find Node classes in the imported modules, including nested classes, avoiding recursion issues."""
        node_classes = []
        visited_classes: Set[type] = set()
        
        def safe_search_class(cls: Any):
            if cls in visited_classes:
                return
            visited_classes.add(cls)
            
            if inspect.isclass(cls) and "Node" in cls.__name__:
                node_classes.append(cls)
            
            # Search for nested classes
            for name, obj in cls.__dict__.items():
                if inspect.isclass(obj) and obj != cls and obj not in visited_classes:
                    safe_search_class(obj)

        for module in self.modules:
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj not in visited_classes:
                    safe_search_class(obj)

        if not node_classes:
            raise ValueError("No Node classes found in the modules.")
        return node_classes

    def _inspect_node_properties(self) -> Dict[str, Any]:
        """Inspect Node class properties across all modules."""
        properties = {}
        for node_class in self.node_classes:
            for name, obj in inspect.getmembers(node_class):
                if not name.startswith("_"):  # Exclude private attributes
                    if isinstance(obj, property) or not callable(obj):
                        properties[name] = obj
        return properties

    def _add_adjectives(self):
        """Add adjectives based on Node properties from all modules."""
        properties = self._inspect_node_properties()
        for name, value in properties.items():
            if isinstance(value, bool):
                self.framework.add_adjective(
                    BooleanAdjective(name, f"node.{name}")
                )
            else:
                self.framework.add_adjective(
                    PointerAdjective(name, f"node.{name}")
                )

    def _add_comparison_adjectives(self):
        """Add comparison adjectives for numeric properties."""
        properties = self._inspect_node_properties()
        for name, value in properties.items():
            if isinstance(value, (int, float)):
                self.framework.add_adjective(
                    ComparisonAdjective(f"better_{name}", name, ">")
                )

    def _analyze_code_for_explanations(self):
        """Analyze the source code of all modules to generate detailed explanations and identify group operations."""
        for module in self.modules:
            source = inspect.getsource(module)
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._analyze_function(node)
                elif isinstance(node, ast.Assign):
                    self._analyze_assignment(node)

    def _analyze_function(self, func_node: ast.FunctionDef):
        """Analyze a function to identify key decision points and group operations."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                self._analyze_condition(node.test)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['max', 'min']:
                    self._analyze_group_operation(node)

    def _analyze_assignment(self, assign_node: ast.Assign):
        """Analyze an assignment to generate explanations for adjectives."""
        target = assign_node.targets[0]
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
            attr_name = target.attr
            explanation = self._generate_explanation_from_assignment(assign_node.value)
            if explanation:
                adjective = self.framework.get_adjective(attr_name)
                if adjective:
                    adjective.explanation = explanation

    def _analyze_condition(self, condition_node: ast.AST):
        """Analyze a condition to generate explanations for affected adjectives."""
        condition_str = ast.unparse(condition_node)
        affected_adjectives = self._find_affected_adjectives(condition_str)
        for adj_name in affected_adjectives:
            adjective = self.framework.get_adjective(adj_name)
            if adjective:
                explanation = ConditionalExplanation(
                    Possession(self._get_condition_from_compare(condition_node)),
                    Assumption(f"This condition affects the '{adj_name}' property: {condition_str}"),
                    Assumption(f"This condition does not affect the '{adj_name}' property")
                )
                adjective.explanation = CompositeExplanation(adjective.explanation, explanation)

    def _analyze_group_operation(self, call_node: ast.Call):
        """Analyze a group operation (max/min) to create appropriate adjectives."""
        if len(call_node.args) == 1 and isinstance(call_node.args[0], ast.Name):
            group_name = call_node.args[0].id
            operation = call_node.func.id
            self.framework.add_adjective(
                PointerAdjective(f"{group_name}_group", f"node.{group_name}")
            )
            if operation == 'max':
                self.framework.add_adjective(
                    MaxRankAdjective(f"max_{group_name}", "better", f"{group_name}_group")
                )
            elif operation == 'min':
                self.framework.add_adjective(
                    MinRankAdjective(f"min_{group_name}", "better", f"{group_name}_group")
                )

    def _generate_explanation_from_assignment(self, value_node: ast.AST) -> Explanation:
        """Generate an explanation based on the right side of an assignment."""
        if isinstance(value_node, ast.Call):
            return Assumption(f"This value is calculated by calling the function: {ast.unparse(value_node.func)}")
        elif isinstance(value_node, ast.BinOp):
            return Assumption(f"This value is the result of the calculation: {ast.unparse(value_node)}")
        elif isinstance(value_node, ast.Compare):
            return ConditionalExplanation(
                Possession(self._get_condition_from_compare(value_node)),
                Assumption("The condition is true"),
                Assumption("The condition is false")
            )
        return None

    def _get_condition_from_compare(self, compare_node: ast.Compare) -> str:
        """Extract the condition from a comparison node."""
        return ast.unparse(compare_node)

    def _find_affected_adjectives(self, condition_str: str) -> List[str]:
        """Find adjectives that are affected by a given condition."""
        return [adj.name for adj in self.framework.adjectives.values() if adj.name in condition_str]

# Usage
if __name__ == "__main__":
    declarator = MultiModuleTreeSearchDeclarator(["src.search.minmax", "src.game.game_tree"])
    framework = declarator.declare_algorithm()
    # Now you can use the framework to explain decisions made by the algorithm