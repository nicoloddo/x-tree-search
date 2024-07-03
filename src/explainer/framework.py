from typing import Dict

class ArgumentationSettings:
    def __init__(self):
        """
        Explanations settings:

        - explanation_depth : 
        Sets the depth of explanations, how deep towards the assumptions it should go.

        - assumptions_verbosity: 
        Set to 'verbose', 'minimal' or 'no'.
        The setting decides how much of the assumptions to print.

        - repeat_explanations:
        Set the repeat_explanations setting to False if you don't want to
        repeat explanations for every node. Explanations of the same adjective are
        usually analogous, explaining one node can suffice to understand the others.
        (conditional explanations are by default zeroed for new nodes because
        they can change depending on the node. Non conditional explanations will 
        mostly be the same even for different nodes.)
        """        

        self._settings = {
            'explanation_depth': 8,
            'assumptions_verbosity': 'no',
            'repeat_explanations': True
        }

    def __getattr__(self, name):
        if name in self._settings:
            return self._settings[name]
        raise AttributeError(f"'ArgumentationSettings' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self._settings:
            self._settings[name] = self._validators[name](self, value)
        else:
            raise AttributeError(f"'ArgumentationSettings' object has no attribute '{name}'")

    def _validate_explanation_depth(self, value):
        if not isinstance(value, int) or value < 1:
            raise ValueError("Explanation depth must be a positive integer.")
        return value

    def _validate_assumptions_verbosity(self, value):
        allowed_values = ['verbose', 'minimal', 'no']
        if value not in allowed_values:
            raise ValueError(f"Assumptions verbosity must be one of: {', '.join(allowed_values)}")
        return value

    def _validate_boolean(self, value):
        return bool(value)

    _validators = {
        'explanation_depth': _validate_explanation_depth,
        'assumptions_verbosity': _validate_assumptions_verbosity,
        'repeat_explanations': _validate_boolean
    }

    def configure(self, settings_dict):
        """Configure settings using a dictionary."""
        for key, value in settings_dict.items():
            setattr(self, key, value)

    def to_dict(self):
        """Return a dictionary representation of the settings."""
        return self._settings.copy()


class ArgumentationFramework:
    """Manages adjectives and their relationships in the argumentation framework."""
    
    def __init__(self):
        """Initialize the ArgumentationFramework."""
        self.adjectives: Dict[str, 'Adjective'] = {}
        self.tree_search_motivation: str = ""
        self.settings = ArgumentationSettings()

    def __getattr__(self, name):
        if hasattr(self.settings, name):
            return getattr(self.settings, name)
        raise AttributeError(f"'ArgumentationFramework' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ('adjectives', 'tree_search_motivation', 'settings'):
            super().__setattr__(name, value)
        elif hasattr(self, 'settings') and hasattr(self.settings, name):
            setattr(self.settings, name, value)
        else:
            super().__setattr__(name, value)

    def configure_settings(self, settings_dict):
        """Configure settings using a dictionary."""
        self.settings.configure(settings_dict)

    def add_adjective(self, adjective: 'Adjective'):
        """
        Add an adjective to the framework and create derived adjectives if it's a ranking adjective.
        
        Args:
            adjective: The Adjective object to add.
        """
        self.adjectives[adjective.name] = adjective
        adjective.set_belonging_framework(self)

    def rename_adjective(self, old_name: str, new_name: str):
        """
        Rename an adjective in the framework.
        
        Args:
            old_name: The current name of the adjective.
            new_name: The new name for the adjective.
        
        Raises:
            ValueError: If no adjective with the old_name is found.
        """
        if old_name in self.adjectives:
            adjective = self.adjectives.pop(old_name)
            adjective.name = new_name
            self.adjectives[new_name] = adjective
        else:
            raise ValueError(f"No adjective named '{old_name}' found.")

    def get_adjective(self, name: str) -> 'Adjective':
        """
        Retrieve an adjective from the framework.
        
        Args:
            name: The name of the adjective to retrieve.
        
        Returns:
            The Adjective object with the given name.
        
        Raises:
            KeyError: If no adjective with the given name is found.
        """
        return self.adjectives[name]

    def _initialize_adjectives_explanations(self):
        for adjective in self.adjectives.values():
            adjective.initialize_explanation()

    def __str__(self):
        propositions = [adjective.proposition().__str__() for adjective in self.adjectives.values()]
        implications = [adjective.implies().__str__() for adjective in self.adjectives.values()]
        
        framework_string = 'Propositions:\n' + '\n'.join(propositions) + '\n\n\nImplications:\n' + '\n'.join(implications)
        return framework_string