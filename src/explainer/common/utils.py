def return_arguments(*args):
    if len(args) == 1:
        return args[0]
    return args

def apply_explanation_tactics(evaluating_object, scope, explanation_tactics, *args):
    if explanation_tactics is None:
        explanation_tactics = {}
        
    for tactic in explanation_tactics.values():
        result = tactic.apply(evaluating_object, scope, *args)
        args = result if isinstance(result, tuple) else (result,)
    return return_arguments(*args)