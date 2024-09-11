from typing import Dict, List, Tuple, Optional

from src.explainer.explanation_settings import ExplanationSettings

class ArgumentationFramework:
    """Manages adjectives and their relationships in the argumentation framework."""
    
    def __init__(self, *, refer_to_nodes_as, adjectives = [], tactics = [], settings: Dict = None):
        """Initialize the ArgumentationFramework.
        
        Args:
            refer_to_nodes_as: How to refer to nodes when printing explanations, e.g.: node, move, position, ...
            adjectives: List of adjectives of the framework
            tactics: List of explanation tactics for the framework (generally applicable over all adjectives)
                    Use adjective specific explanation tactics if you want to constrain a tactc.
            settings: Dictionary of framework specific settings. """
        
        self.tree_search_motivation: str = ""

        self.refer_to_nodes_as = refer_to_nodes_as

        self.adjectives: Dict[str, 'Adjective'] = {}
        self.add_adjectives(adjectives)

        self.general_explanation_tactics = {}
        self.add_explanation_tactics(tactics)

        self.framework_specific_settings = False
        self.set_settings(settings)
    
    def set_settings(self, settings_dict: Dict = None):
        """Set framework specific settings giving a dictionary."""
        self.settings = ExplanationSettings()

        if settings_dict is not None:
            self.framework_specific_settings = True
            self.settings.configure(settings_dict)

    def actuate_settings(self):
        self.settings.actuate_all()
        
    def _set_settings(self, settings):
        """Method used by the explainer to accord the settings to the explainer.
        Only works if the framework does not have framework specific settings."""
        if not self.framework_specific_settings:
            self.settings = settings

    def add_adjective(self, adjective: 'Adjective'):
        """
        Add an adjective to the framework.
        
        Args:
            adjective: The Adjective object to add.
        """
        self.adjectives[adjective.name] = adjective
        adjective.contextualize(self)

    def del_adjective(self, adjective_name: str):
        """
        Deletes an adjective from the framework.
        
        Args:
            adjective: The Adjective object to add.
        """
        adjective = self.adjectives[adjective_name]
        adjective.decontextualize()
        del self.adjectives[adjective_name]
    
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
    
    def add_explanation_tactics_to_adjective(self, to_adjective:str, tactics: List['Tactic']):
        """Adds explanation tactics to a specified adjective."""
        tactic_tuples = []
        for tactic in tactics:
            tactic_tuples.append((tactic, to_adjective))

        self.add_explanation_tactics(tactic_tuples)
    
    def add_explanation_tactics(self, tactics: List['Tactic' | Tuple['Tactic', str]]):
        """Adds explanation tactics from a list of tactics or tuple of tactic and adjective to add it to."""
        for tactic_input in tactics:
            if isinstance(tactic_input, tuple):
                tactic = tactic_input[0]
                to_adjective = tactic_input[1]
                self.add_explanation_tactic(tactic, to_adjective=to_adjective)
            else:
                tactic = tactic_input
                self.add_explanation_tactic(tactic)
    
    def add_explanation_tactic(self, tactic: 'Tactic', *, to_adjective: str = ''):
        if to_adjective != '':
            adjective = self.get_adjective(to_adjective)
            adjective.add_explanation_tactic(tactic)
            return

        tactics_to_add = [tactic]
        tactics_to_add += tactic.get_requirements()
        self._add_explanation_tactics(tactics_to_add)
            
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