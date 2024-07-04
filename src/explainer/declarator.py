import sys
import os
import trace
import inspect

import importlib
import inspect
import ast
import textwrap
from typing import Any, Dict, List, Set, Tuple

from src.explainer.framework import ArgumentationFramework

def get_dedented_source(module):
    source = inspect.getsource(module)
    return textwrap.dedent(source)

class VariableTracer:
    def __init__(self, variable_names, allowed_modules=None):
        self.variable_names = variable_names
        self.variable_history = {var: [] for var in variable_names}
        self.allowed_modules = allowed_modules or []
        self.current_directory = os.getcwd()

    def trace_calls(self, frame, event, arg):
        # Check if the module is allowed
        module_name = frame.f_globals.get('__name__', '')
        filename = frame.f_code.co_filename
        module_name = self.filename_to_module(filename)
        if self.is_custom_module(module_name):
            return self.local_trace

    def local_trace(self, frame, event, arg):
        if event == 'line':
            # Check the module of the current frame
            filename = frame.f_code.co_filename
            module_name = self.filename_to_module(filename)
            if self.is_custom_module(module_name):
                print("Inside " + module_name)
                line_number = frame.f_lineno
                code_context = frame.f_code
                local_vars = frame.f_locals

                for var in self.variable_names:
                    print(var)
                    if var in local_vars:
                        value = local_vars[var]
                        try:
                            source_lines, starting_line = inspect.getsourcelines(code_context)
                            if starting_line <= line_number < starting_line + len(source_lines):
                                source_line = source_lines[line_number - starting_line].strip()
                            else:
                                source_line = "<source line not available>"
                        except Exception as e:
                            source_line = f"<error retrieving source: {e}>"
                        
                        self.variable_history[var].append((line_number, source_line, value))

        return self.local_trace

    def filename_to_module(self, filename):
        # Normalize the file path to module name
        relative_path = os.path.relpath(filename, self.current_directory)
        return relative_path.replace(os.path.sep, '.').rsplit('.', 1)[0]

    def is_custom_module(self, module_name):
        # Check if the module name is in the allowed modules
        return any(module_name.startswith(allowed_module) for allowed_module in self.allowed_modules)

    def start(self):
        sys.settrace(self.trace_calls)

    def stop(self):
        sys.settrace(None)

    def get_variable_history(self):
        return self.variable_history

class TreeSearchDeclarator:
    def __init__(self, module_names: List[str], search_algorithm, game_tree):
        self.module_names = module_names
        self.modules = [importlib.import_module(name) for name in module_names]
        self.framework = ArgumentationFramework()
        self.node_classes = self._find_node_classes()
        self.source_code = self._collect_source_code()
        self.class_asts = self._parse_class_asts()
        self.node_properties = self._find_node_properties()
        self.search = search_algorithm
        self.game_tree = game_tree

    def _collect_source_code(self) -> str:
        """Collect all source code from all modules."""
        all_source = ""
        for module in self.modules:
            all_source += get_dedented_source(module) + "\n\n"
        return all_source

    def _parse_class_asts(self) -> Dict[str, ast.ClassDef]:
        """Parse ASTs for all classes, including nested classes."""
        class_asts = {}
        visited_classes: Set[str] = set()

        def safe_search_class(cls: Any, parent_name: str = ""):
            if cls.__name__ in visited_classes:
                return
            visited_classes.add(cls.__name__)

            full_name = f"{parent_name}.{cls.__name__}" if parent_name else cls.__name__
            
            # Get the source code of the class
            try:
                source = get_dedented_source(cls)
                class_ast = ast.parse(source).body[0]  # The class definition should be the first item
                class_asts[full_name] = class_ast
            except (OSError, TypeError):
                # This can happen for built-in classes or those without source
                pass

            # Search for nested classes
            for name, obj in cls.__dict__.items():
                if inspect.isclass(obj) and obj != cls and obj.__name__ not in visited_classes:
                    safe_search_class(obj, full_name)

        for module in self.modules:
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj.__name__ not in visited_classes:
                    safe_search_class(obj)

        return class_asts

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

    def _find_node_properties(self) -> Dict[str, Tuple[Any, ast.ClassDef]]:
        """Inspect Node class properties and attributes across all modules."""
        properties = {}
        for node_class in self.node_classes:
            class_ast = self.class_asts[node_class.__qualname__]
            
            # Inspect class attributes
            for name, value in node_class.__dict__.items():
                if not name.startswith("_"):
                    properties[name] = (value, class_ast)

            # Inspect instance attributes from __init__ method
            init_method = next((m for m in class_ast.body if isinstance(m, ast.FunctionDef) and m.name == '__init__'), None)
            if init_method:
                for node in ast.walk(init_method):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                        properties[node.attr] = (None, class_ast)

            # Inspect properties
            for name, obj in inspect.getmembers(node_class):
                if isinstance(obj, property) and not name.startswith("_"):
                    properties[name] = (obj, class_ast)

        return properties

    def trace_properties(self):
        variable_names = list(self.node_properties.keys())
        tracer = VariableTracer(variable_names, self.module_names)
        tracer.start()
        self.search.run(self.game_tree.root.id, 2)
        tracer.stop()

        return list(self.node_properties.keys()), tracer.get_variable_history()