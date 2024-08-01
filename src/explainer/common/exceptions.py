class CannotBeEvaluated(Exception):
    """When a predicate cannot be evaluated on a node."""
    
    def __init__(self, message="Predicate cannot be evaluated."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"CannotBeEvaluated: {self.message}"