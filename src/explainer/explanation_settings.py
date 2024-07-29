class ExplanationSettings:
    def __init__(self):
        """
        Explanation settings:

        - refer_to_nodes_as :
        How to refer to nodes when printing explanations, e.g.: node, move, position, ...

        - explanation_depth : 
        Sets the depth of explanations, how deep towards the assumptions it should go.

        - assumptions_verbosity: 
        Set to 'verbose', 'minimal', 'no' or 'if_asked.
        The setting decides how much of the assumptions to print.

        - print_depth:
        Set to True or False.
        Decided if you want to explicitly print the depth at each explanation step.
        Useful for debugging purposes and clarify on the explanation's recursion.
        """        

        self._settings = {
            'refer_to_nodes_as' : 'node',
            'explanation_depth': 8,
            'assumptions_verbosity': 'if_asked',
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
        allowed_values = ['verbose', 'minimal', 'no', 'if_asked']
        if value not in allowed_values:
            raise ValueError(f"Assumptions verbosity must be one of: {', '.join(allowed_values)}")

    def _validate_boolean(self, value):
        if not isinstance(value, bool):
            raise ValueError("Tried to set a Boolean setting to a non boolean value.")
    
    def _validate_string(self, value):
        if not isinstance(value, str):
            raise ValueError("Tried to set a String setting to a non string value.")

    _validators = {
        'refer_to_nodes_as': _validate_string,
        'explanation_depth': _validate_explanation_depth,
        'assumptions_verbosity': _validate_assumptions_verbosity,
        'print_depth': _validate_boolean
    }

    def _actuate_passthrough(self, value):
        return value
    
    def _actuate_print_depth(self, value):
        return value
    
    _actuators = {
        'refer_to_nodes_as': _actuate_passthrough,
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