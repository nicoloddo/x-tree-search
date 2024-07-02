from typing import Dict

class ArgumentationFramework:
    """Manages adjectives and their relationships in the argumentation framework."""
    
    def __init__(self):
        """Initialize the ArgumentationFramework."""
        self.adjectives: Dict[str, 'Adjective'] = {}
        self.tree_search_motivation: str = ""

        """Explanations settings"""

        """How deep in the explanation we want to go"""
        self.explanation_depth = 3

        """Set to 'verbose', 'minimal' or 'no'
        The setting decides how much of the assumptions to print."""
        self.assumptions_verbosity = 'no'

        """Set the repeat_expl_per_node setting to False if you don't want to
        repeat explanations for every node. Explanations of the same adjective are
        usually analogous, explaining one node can suffice to understand the others.
        (conditional explanations are by default zeroed for new nodes because
        they can change depending on the node. Non conditional explanations will 
        mostly be the same even for different nodes.)"""
        self.repeat_expl_per_node = False

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

    def __str__(self):
        propositions = [adjective.proposition().__str__() for adjective in self.adjectives.values()]
        implications = [adjective.implies().__str__() for adjective in self.adjectives.values()]
        
        framework_string = '\n\n'.join(propositions) + '\n\nImplications:\n' + '\n\n'.join(implications)
        return framework_string