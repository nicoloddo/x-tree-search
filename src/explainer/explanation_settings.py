from src.explainer.propositional_logic import LogicalExpression

EXPLANATION_DEPTH_ALLOWED_VALUES = list(range(0, 10))
def _validate_explanation_depth(value):
    if not isinstance(value, int) or value not in EXPLANATION_DEPTH_ALLOWED_VALUES:
        raise ValueError(f"Explanation depth must be a positive integer or 0.")

ASSUMPTIONS_VERBOSITY_ALLOWED_VALUES = ['verbose', 'minimal', 'no', 'if_asked']
def _validate_assumptions_verbosity(value):
    if value not in ASSUMPTIONS_VERBOSITY_ALLOWED_VALUES:
        raise ValueError(f"Assumptions verbosity must be one of: {', '.join(ASSUMPTIONS_VERBOSITY_ALLOWED_VALUES)}")

def _validate_boolean(value):
    if not isinstance(value, bool):
        raise ValueError("Tried to set a Boolean setting to a non boolean value.")

def _validate_string(value):
    if not isinstance(value, str):
        raise ValueError("Tried to set a String setting to a non string value.")

PRINT_MODE_ALLOWED_VALUES = ['logic', 'verbal']
def _validate_print_mode(value):
    if value not in PRINT_MODE_ALLOWED_VALUES:
        raise ValueError(f"Print mode must be one of: {', '.join(PRINT_MODE_ALLOWED_VALUES)}")

class ExplanationSettings:
    """
    Explanation settings:

    - with_framework: Set to a string.
    Decides the name of the framework to use in the explanations.

    - explanation_depth: Set to an integer.
    Decides how deep towards the assumptions the explanation should go.

    - assumptions_verbosity: Set to 'verbose', 'minimal', 'no' or 'if_asked'.
    Decides how much of the assumptions to print.

    - print_depth: Set to True or False.
    Decides if you want to explicitly print the depth at each explanation step.
    Useful for debugging purposes and clarify on the explanation's recursion.

    - print_implicit_assumptions: Set to True or False.
    Decides if you want to print the implicit assumptions.
    Implicit assumptions are assumptions that are often not necessary to be stated explicitly.
    Internal explanations' assumptions are always implicit. 
    Assumptions added by the user are by default explicit, but they can be set to implicit in the Assumption constructor.

    - print_mode: Set to 'logic' or 'verbal'.
    Decides if you want to print the explanation in logic form or verbally in natural language.
    """  
    def __init__(self):
        self._settings = {
            'with_framework' : None,
            'explanation_depth': 8,
            'assumptions_verbosity': 'if_asked',
            'print_depth': False,
            'print_implicit_assumptions': True,
            'print_mode': 'logic'
        }

    _validators = {
        'with_framework': _validate_string,
        'explanation_depth': _validate_explanation_depth,
        'assumptions_verbosity': _validate_assumptions_verbosity,
        'print_depth': _validate_boolean,
        'print_implicit_assumptions': _validate_boolean,
        'print_mode': _validate_print_mode
    }

    def _actuate_passthrough(self, value):
        return value
    
    def _actuate_print_mode(self, value):
        LogicalExpression.print_mode = value
        return self._actuate_passthrough(value)
    
    _actuators = {
        'with_framework': _actuate_passthrough,
        'explanation_depth': _actuate_passthrough,
        'assumptions_verbosity': _actuate_passthrough,
        'print_depth': _actuate_passthrough,
        'print_implicit_assumptions': _actuate_passthrough,
        'print_mode': _actuate_print_mode
    }

    def __getattr__(self, name):
        if name in self._settings:
            return self._settings[name]
        raise AttributeError(f"'ArgumentationSettings' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self._settings:
            self._validators[name](value)
            self._settings[name] = self._actuators[name](self, value)
        else:
            raise AttributeError(f"'ArgumentationSettings' object has no attribute '{name}'")

    def configure(self, settings_dict):
        """Configure settings using a dictionary."""
        for key, value in settings_dict.items():
            setattr(self, key, value)

    def to_dict(self):
        """Return a dictionary representation of the settings."""
        return self._settings.copy()

    def actuate_all(self):
        for key, value in self._settings.items():
            self._actuators[key](self, value)