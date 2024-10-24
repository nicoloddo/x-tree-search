class CannotBeEvaluated(Exception):
    """When a predicate cannot be evaluated on a node."""
    
    def __init__(self, adjective_name = None, evaluated_on = None, refer_to_nodes_as = None, *, message_override = None):
        if message_override is not None:
            self.adjective_name = None
            self.message = message_override
        else:
            if adjective_name is None:
                raise ValueError("CannotBeEvaluated exception must have an adjective name or a message override.")
            self.adjective_name = adjective_name
            self.refer_to_nodes_as = refer_to_nodes_as or 'node'
            evaluated_on = evaluated_on or []
            evaluated_on_str = ", ".join(str(arg) for arg in evaluated_on)
            self.message = f"The adjective \"{self.adjective_name}\" cannot be evaluated on {evaluated_on_str}."
        super().__init__(self.message)

    def __str__(self):
        return self.message