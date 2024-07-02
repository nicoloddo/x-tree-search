from typing import Any, Callable

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
        self.framework = framework
        self.getters = {}

    def set_getter(self, adjective_name: str, getter: Callable[[Any], Any]):
        self.framework.get_adjective(adjective_name)._set_getter(getter)

    def evaluate(self, node: Any, adjective_name: str, comparison_node: Any = None) -> bool:
        adjective = self.framework.get_adjective(adjective_name)

        if comparison_node:
            adjective.evaluate(node, comparison_node)
        else:
            adjective.evaluate(node, context=self)

    def explain_adjective(self, node: Any, adjective_name: str, comparison_node: Any = None) -> Any:
        """
        Generate a propositional logic explanation for why a node has a specific adjective.
        
        Args:
            node: The node to explain.
            adjective_name: The name of the adjective to explain.
            comparison_node: The other node involved in a comparison (if it is a comparison)
        
        Returns:
            A Implies implication representing the explanation of the adjective's affirmation.
        
        Raises:
            KeyError: If no adjective with the given name is found.
        """
        adjective = self.framework.get_adjective(adjective_name)
        #adjective.initialize_explanation()
        if not comparison_node: # The adjective is not comparative
            explanation = adjective.explain(node)
        else:
            explanation = adjective.explain(node, comparison_node)

        return explanation


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
            return self.explain_adjective(node, adjective_name)
        else:
            return #Implies("Invalid query format. Please use 'Why does [node] have [adjective]?'")

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