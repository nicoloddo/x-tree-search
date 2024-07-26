from typing import Any, Callable
from src.explainer.propositional_logic import Implies

STARTING_EXPLANATION_DEPTH = 1

class ExplanationSettings:
    def __init__(self):
        """
        Explanation settings:

        - explanation_depth : 
        Sets the depth of explanations, how deep towards the assumptions it should go.

        - assumptions_verbosity: 
        Set to 'verbose', 'minimal' or 'no'.
        The setting decides how much of the assumptions to print.

        - print_depth:
        Set to True or False.
        Decided if you want to explicitly print the depth at each explanation step.
        Useful for debugging purposes and clarify on the explanation's recursion.
        """        

        self._settings = {
            'explanation_depth': 8,
            'assumptions_verbosity': 'no',
            'print_depth': False
        }

    def __getattr__(self, name):
        if name in self._settings:
            return self._settings[name]
        raise AttributeError(f"'ArgumentationSettings' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self._settings:
            self._validators[name](self, value)
            self._settings[name] = self._actuators[name](self, value)
        else:
            raise AttributeError(f"'ArgumentationSettings' object has no attribute '{name}'")

    def _validate_explanation_depth(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Explanation depth must be a positive integer or 0.")

    def _validate_assumptions_verbosity(self, value):
        allowed_values = ['verbose', 'minimal', 'no']
        if value not in allowed_values:
            raise ValueError(f"Assumptions verbosity must be one of: {', '.join(allowed_values)}")

    def _validate_boolean(self, value):
        if not isinstance(value, bool):
            raise ValueError("Tried to set a Boolean setting to a non boolean value.")

    _validators = {
        'explanation_depth': _validate_explanation_depth,
        'assumptions_verbosity': _validate_assumptions_verbosity,
        'print_depth': _validate_boolean
    }

    def _actuate_passthrough(self, value):
        return value
    
    def _actuate_print_depth(self, value):
        return value
    
    _actuators = {
        'explanation_depth': _actuate_passthrough,
        'assumptions_verbosity': _actuate_passthrough,
        'print_depth': _actuate_print_depth
    }

    def configure(self, settings_dict):
        """Configure settings using a dictionary."""
        for key, value in settings_dict.items():
            setattr(self, key, value)

    def to_dict(self):
        """Return a dictionary representation of the settings."""
        return self._settings.copy()
    
class ArgumentativeExplainer:
    """
    Generates explanations based on the argumentation framework.
    It is suggested to provide a __str__(self) method in the node classes
    to print the nodes correctly.
    """
    
    def __init__(self, framework: 'ArgumentationFramework'):
        """
        Initialize the ArgumentativeExplainer.
        
        Args:
            framework: The ArgumentationFramework to use for explanations.
        """
        self.settings = ExplanationSettings()

        self.framework = framework
        self.framework.settings = self.settings
        self.getters = {}

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

    def explain_adjective(self, node: Any, adjective_name: str, comparison_node: Any = None, *, explanation_depth = None, print_depth = False) -> Any:
        """
        Generate a propositional logic explanation for why a node has a specific adjective.
        
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
        # Handle temporary settings for this explanation:
        if explanation_depth is not None:
            prev_explanation_depth = self.settings.explanation_depth
            prev_print_depth = self.settings.print_depth

            self.settings.explanation_depth = explanation_depth
            self.settings.print_depth = print_depth

        # Get the explanation
        adjective = self.framework.get_adjective(adjective_name)
        if not comparison_node: # The adjective is not comparative
            explanation = adjective.explain(node, current_explanation_depth = STARTING_EXPLANATION_DEPTH)
        else:
            explanation = adjective.explain(node, comparison_node, current_explanation_depth = STARTING_EXPLANATION_DEPTH)

        # Give the explanation
        if isinstance(explanation, Implies):
            explanation._str_settings(print_first = True)
        print(explanation)
        
        # Reset settings for future explanations:
        if explanation_depth is not None:
            self.settings.explanation_depth = prev_explanation_depth
            self.settings.print_depth = prev_print_depth

    def add_explanation_tactic(self, adjective_name: str, tactic: 'Tactic'):
        adjective = self.framework.get_adjective(adjective_name)
        adjective.explanation.add_explanation_tactic(tactic)

    def del_explanation_tactic(self, adjective_name: str, tactic_class_name: str):
        adjective = self.framework.get_adjective(adjective_name)
        adjective.explanation.del_explanation_tactic(tactic_class_name)

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