class CannotBeEvaluated(Exception):
    """When a predicate cannot be evaluated on a node."""
    
    def __init__(self, adjective_name, args, refer_to_nodes_as):
        self.adjective_name = adjective_name
        self.refer_to_nodes_as = refer_to_nodes_as
        args_string = ", ".join(str(arg) for arg in args)
        self.message = f"The adjective \"{self.adjective_name}\" cannot be evaluated on {args_string}."
        super().__init__(self.message)

    def __str__(self):
        return self.message