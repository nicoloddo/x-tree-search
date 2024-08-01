from typing import Dict, List

from src.explainer.explanation_settings import ExplanationSettings

class ArgumentationFramework:
    """Manages adjectives and their relationships in the argumentation framework."""
    
    def __init__(self, *, refer_to_nodes_as):
        """Initialize the ArgumentationFramework.
        
        Args:
            refer_to_nodes_as: How to refer to nodes when printing explanations, e.g.: node, move, position, ..."""
        
        self.adjectives: Dict[str, 'Adjective'] = {}
        self.tree_search_motivation: str = ""
        self.settings = ExplanationSettings()
        self.refer_to_nodes_as = refer_to_nodes_as
        self.general_explanation_tactics = {}
    
    def set_settings(self, settings):
        self.settings = settings

    def add_adjective(self, adjective: 'Adjective'):
        """
        Add an adjective to the framework and create derived adjectives if it's a ranking adjective.
        
        Args:
            adjective: The Adjective object to add.
        """
        self.adjectives[adjective.name] = adjective
        adjective.set_belonging_framework(self)
    
    def add_adjectives(self, adjectives: List['Adjective']):
        """
        Add multiple adjectives to the framework all together.
        
        Args:
            adjectives: The List of Adjective objects to add.
        """
        for adjective in adjectives:
            self.add_adjective(adjective)

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
    
    def add_explanation_tactic(self, tactic: 'Tactic', *, to_adjective: str = ''):
        tactics_to_add = [tactic]
        for requirement in tactic.requirements:
            tactics_to_add.append(requirement[0](*requirement[1]))

        if to_adjective == '':
            self._add_explanation_tactics(tactics_to_add)
        else:
            adjective = self.get_adjective(to_adjective)
            adjective._add_explanation_tactics(tactics_to_add)

    def del_explanation_tactic(self, tactic_class_name: str, *, to_adjective: str = ''):
        if to_adjective == '':
            tactic = self.get_explanation_tactic(tactic_class_name)
        else:
            adjective = self.get_adjective(to_adjective)
            tactic = adjective.get_explanation_tactic(tactic_class_name)

        tactics_to_delete_names = [tactic_class_name]
        for requirement in tactic.requirements:
            tactics_to_delete_names.append(requirement.name)

        if to_adjective == '':
            self._del_explanation_tactics(tactics_to_delete_names)
        else:
            adjective._del_explanation_tactics(tactics_to_delete_names)

    def _add_explanation_tactics(self, tactics):
        for tactic in tactics:
            tactic.contextualize(self)
            self.general_explanation_tactics[tactic.name] = tactic
    
    def _del_explanation_tactics(self, tactic_names):
        for tactic_name in tactic_names:
            del self.general_explanation_tactics[tactic_name]

    def get_explanation_tactic(self, tactic_name):
        return self.general_explanation_tactics[tactic_name]
    
    def __str__(self):
        propositions = [adjective.proposition().__str__() for adjective in self.adjectives.values()]
        implications = [adjective.implies().__str__() for adjective in self.adjectives.values()]
        
        framework_string = 'Propositions:\n' + '\n'.join(propositions) + '\n\n\nImplications:\n' + '\n'.join(implications)
        return framework_string