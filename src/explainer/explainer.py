from typing import Any, Callable
from src.explainer.propositional_logic import Implies

from src.explainer.explanation_settings import ExplanationSettings
from src.explainer.common.exceptions import CannotBeEvaluated

STARTING_EXPLANATION_DEPTH = 1
    
class ArgumentativeExplainer:
    """
    Generates explanations based on the argumentation framework.
    It is suggested to provide a __str__(self) method in the node classes
    to print the nodes correctly.
    """
    
    def __init__(self):
        """
        Initialize the ArgumentativeExplainer.
        
        Args:
            framework: The ArgumentationFramework to use for explanations.
        """
        self.settings = ExplanationSettings()

        self.framework = None
        self.frameworks = {}

        self.getters = {}

    def add_framework(self, framework_name: str, framework: 'ArgumentationFramework'):
        """
        Add a framework to explain the tree search.
        """
        self.frameworks[framework_name] = framework
        framework._set_settings(self.settings)

        if len(self.frameworks) == 1: 
            # If this was the first added framework, select it automatically
            self.settings.with_framework = framework_name
            self.select_framework(framework_name)
    
    def select_framework(self, framework_name: str):
        """
        Selects the framework to use for the explanations
        """
        self.framework = self.frameworks[framework_name]
        self.framework.actuate_settings()

    def available_frameworks(self):
        for framework in self.frameworks.keys():
            print(framework)

    def __getitem__(self, key):
        """
        Allow accessing frameworks using square bracket notation.

        Args:
            key: The name of the framework to access.

        Returns:
            The framework associated with the given key.

        Raises:
            KeyError: If the framework name is not found.
        """
        try:
            return self.frameworks[key]
        except KeyError:
            raise KeyError(f"Framework '{key}' not found in ArgumentativeExplainer")

    def set_getter(self, adjective_name: str, getter: Callable[[Any], Any]):
        """Overrides the getter function setted during the adjective declaration.
        Be aware that no safeness checks are performed when setting the getter directly."""
        self.framework.get_adjective(adjective_name)._set_getter(getter)

    def evaluate(self, node: Any, adjective_name: str, comparison_node: Any = None) -> bool:
        adjective = self.framework.get_adjective(adjective_name)

        if comparison_node:
            adjective.evaluate(node, comparison_node)
        else:
            adjective.evaluate(node, context=self)

    def explain_adjective(self, node: Any, adjective_name: str, comparison_node: Any = None, *, with_framework = None, explanation_depth = None, print_depth = None) -> Any:
        """
        Generate a propositional logic explanation for why a node has a specific adjective.
        Put a parent node state attribute to the nodes if you want to print the search node state.
        
        Args:
            node: The node to explain.
            adjective_name: The name of the adjective to explain.
            comparison_node: The other node involved in a comparison (if it is a comparison)
            
            kwargs: Temporary settings, to consider only for this explanation instance.
        
        Returns:
            A Implies implication representing the explanation of the adjective's affirmation.
        
        Raises:
            KeyError: If no adjective with the given name is found.
        """
        if node is None:
            raise ValueError("The node you are asking about is non existent. This might happen because of async processing. Try to run again.")

        # Handle temporary settings for this explanation:
        if with_framework is not None:
            prev_framework = self.settings.with_framework
            self.settings.with_framework = with_framework
            self.select_framework(with_framework)

        if explanation_depth is not None:
            prev_explanation_depth = self.framework.settings.explanation_depth
            self.framework.settings.explanation_depth = explanation_depth

        if print_depth is not None:
            prev_print_depth = self.framework.settings.print_depth
            self.framework.settings.print_depth = print_depth

        # Get the explanation
        to_raise_later = None
        try:
            adjective = self.framework.get_adjective(adjective_name)
            adjective.init_explanations_book()
            if not comparison_node: # The adjective is not comparative
                explanation = adjective.explain(node, current_explanation_depth = STARTING_EXPLANATION_DEPTH)
            else:
                explanation = adjective.explain(node, comparison_node, current_explanation_depth = STARTING_EXPLANATION_DEPTH)

            # Give the explanation
            if isinstance(explanation, Implies):
                explanation._str_settings(print_first = True)

            if hasattr(node, "parent_state"):
                context_str = f"Given:\n {node.parent_state}\n"
            else:
                context_str = ""
            print(f"{context_str}{explanation}")

        except CannotBeEvaluated as e:
            print(f"The adjective \"{adjective_name}\" cannot be evaluated on the {self.framework.refer_to_nodes_as} {node}.")
            if adjective_name != e.adjective_name:
                print(f"That is because {e.message}")

        except Exception as e:
            to_raise_later = e
            print(f"An unexpected error occurred while generating the explanation: {str(e)}")
        
        # IMPORTANT: DO NOT STOP THE EXEC OF THIS METHOD BEFORE RESETTING THE SETTINGS,
        # AVOID return AND UNCATCHED EXCEPTIONS BEFORE THE NEXT BLOCK.

        # Reset settings for future explanations:
        if with_framework is not None:
            self.settings.with_framework = prev_framework
            self.select_framework(prev_framework)

        if explanation_depth is not None:
            self.framework.settings.explanation_depth = prev_explanation_depth

        if print_depth is not None:
            self.framework.settings.print_depth = prev_print_depth

        # Raise unexpected exception
        if to_raise_later is not None:
            raise to_raise_later

    def add_explanation_tactic(self, tactic: 'Tactic', *, to_adjective: str = '', to_framework: str):
        framework = self.frameworks[to_framework]
        if to_adjective == '':
            perform_on = framework
        else:
            adjective = framework.get_adjective(to_adjective)
            perform_on = adjective

        tactics_to_add = [tactic]
        for requirement in tactic.requirements:
            tactics_to_add.append(requirement[0](*requirement[1]))

        perform_on._add_explanation_tactics(tactics_to_add)

    def del_explanation_tactic(self, tactic_class_name: str, *, to_adjective: str = '', to_framework: str):
        framework = self.frameworks[to_framework]
        if to_adjective == '':
            perform_on = framework
        else:
            adjective = framework.get_adjective(to_adjective)
            perform_on = adjective

        tactic = perform_on.get_explanation_tactic(tactic_class_name)

        tactics_to_delete_names = [tactic_class_name]
        for requirement in tactic.get_requirements():
            tactics_to_delete_names.append(requirement.name)

        perform_on._del_explanation_tactics(tactics_to_delete_names)

    def query_explanation(self, node: Any, query: str) -> Any:
        pass
        """
        Generate an explanation for a specific query about a node's adjective.
        
        Args:
            node: The node to explain.
            query: A string query in the format "Why does [node] have [adjective]?"
        
        Returns:
            An implication representing the explanation, or an error message for invalid queries.
        """
        parts = query.lower().split()
        if len(parts) >= 4 and parts[0] == "why" and parts[1] == "does":
            adjective_name = parts[-1].rstrip("?")
            self.explain_adjective(node, adjective_name)
        else:
            return #print(Implies("Invalid query format. Please use 'Why does [node] have [adjective]?'"))

    def set_tree_search_motivation(self, getter: Callable, adjective_name: str):
        pass
        """
        Set the adjective that motivates tree search choices.
        
        Args:
            adjective_name: The name of the adjective to use as motivation.
        
        Raises:
            ValueError: If no adjective with the given name is found.
        """
        if adjective_name not in self.framework.adjectives:
            raise ValueError(f"Adjective '{adjective_name}' not found.")
        #self.tree_search_motivation = adjective_name

    def configure_settings(self, settings_dict):
        """Configure settings using a dictionary."""
        self.settings.configure(settings_dict)

        if 'with_framework' in settings_dict:
            self.select_framework(self.settings.with_framework)