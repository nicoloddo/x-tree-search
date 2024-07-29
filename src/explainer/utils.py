def apply_explanation_tactics(evaluating_object, scope, explanation_tactics, *args, **kwargs):
    if explanation_tactics is None:
        return
    for tactic in explanation_tactics.values():
        tactic.apply(scope, evaluating_object, *args, **kwargs)