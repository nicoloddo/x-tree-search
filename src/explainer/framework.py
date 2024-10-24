from typing import Dict, List, Tuple, Optional, Union

from src.explainer.explanation_settings import ExplanationSettings
from src.explainer.common.utils import AdjectiveType

class ArgumentationFramework:
    """
    Manages adjectives and their relationships in the argumentation framework.

    This class provides functionality to add, remove, and manage adjectives,
    as well as explanation tactics for the framework. It also handles framework-specific
    settings and provides methods for interacting with the framework's components.

    :ivar refer_to_nodes_as: How to refer to nodes when printing explanations.
    :ivar adjectives: A dictionary of :class:`Adjective` objects in the framework with their name as key.
    :ivar general_explanation_tactics: A dictionary of general explanation tactics with their name as key.
    :ivar settings: An :class:`ExplanationSettings` object for framework-specific settings.
    :ivar framework_specific_settings: A boolean indicating if framework-specific settings are used.
    """
    
    def __init__(self, *, refer_to_nodes_as: str, 
                 adjectives: List['Adjective'] = None, main_explanation_adjective: str = None,
                 tactics: List[Union['Tactic', Tuple['Tactic', str]]] = None,
                 settings: Dict = None):
        """
        Initialize the ArgumentationFramework.
        
        :param refer_to_nodes_as: How to refer to nodes when printing explanations, e.g., "node", "move", "position".
        :param adjectives: List of :class:`Adjective` objects for the framework.
        :param main_explanation_adjective: The name of the adjective which explanations may arise first from. 
            The main adjective will be used if no adjective is specified in the explanation request.
        :param tactics: List of explanation tactics for the framework. Can be general or adjective-specific.
        :param settings: Dictionary of framework-specific settings.
        """
        self.refer_to_nodes_as = refer_to_nodes_as
        self.adjectives: Dict[str, 'Adjective'] = {}
        self.add_adjectives(adjectives or [])
        self.set_main_explanation_adjective(main_explanation_adjective)
        self.general_explanation_tactics = {}
        self.add_explanation_tactics(tactics or [])
        self.framework_specific_settings = False
        self.set_settings(settings)
    
    def set_settings(self, settings_dict: Optional[Dict] = None) -> None:
        """
        Set framework-specific settings using a dictionary.

        :param settings_dict: Dictionary containing framework-specific settings.
        """
        self.settings = ExplanationSettings()
        if settings_dict is not None:
            self.framework_specific_settings = True
            self.settings.configure(settings_dict)

    def actuate_settings(self) -> None:
        """
        Activate all settings in the framework.
        """
        self.settings.actuate_all()
        
    def _set_settings(self, settings: ExplanationSettings) -> None:
        """
        Method used by the explainer to accord the settings to the explainer.
        Only works if the framework does not have framework-specific settings.

        :param settings: An :class:`ExplanationSettings` object to be set.
        """
        if not self.framework_specific_settings:
            self.settings = settings

    def set_main_explanation_adjective(self, adjective_name: str) -> None:
        """
        Set the main adjective for the framework.
        """
        self.main_explanation_adjective = adjective_name

    def add_adjective(self, adjective: 'Adjective') -> None:
        """
        Add an adjective to the framework.
        
        :param adjective: The :class:`Adjective` object to add.
        """
        if adjective.type == AdjectiveType.AUXILIARY and adjective.name in self.adjectives:
            self.adjectives[adjective.name].add_getter(adjective.getter[0])
        else:
            self.adjectives[adjective.name] = adjective
            adjective.contextualize(self)

    def del_adjective(self, adjective_name: str) -> None:
        """
        Delete an adjective from the framework.
        
        :param adjective_name: The name of the adjective to delete.
        :raises ValueError: If the Auxiliary Adjective was not used completely.
        """            
        adjective = self.adjectives[adjective_name]
        if adjective.type == AdjectiveType.AUXILIARY:
            if len(adjective.getter) > 0:
                raise ValueError("The Auxiliary Adjective was not used completely? It is not empty.")
        adjective.decontextualize()
        del self.adjectives[adjective_name]
    
    def has_adjective(self, adjective_name: str) -> bool:
        """
        Check if an adjective is in the framework.
        
        :param adjective_name: The name of the adjective to check.
        :return: True if the adjective is in the framework, False otherwise.
        """
        return adjective_name in self.adjectives.keys()
    
    def add_adjectives(self, adjectives: List['Adjective']) -> None:
        """
        Add multiple adjectives to the framework.
        
        :param adjectives: A list of :class:`Adjective` objects to add.
        """
        for adjective in adjectives:
            self.add_adjective(adjective)

    def rename_adjective(self, old_name: str, new_name: str) -> None:
        """
        Rename an adjective in the framework.
        
        :param old_name: The current name of the adjective.
        :param new_name: The new name for the adjective.
        :raises ValueError: If no adjective with the old_name is found.
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
        
        :param name: The name of the adjective to retrieve.
        :return: The :class:`Adjective` object with the given name.
        :raises KeyError: If no adjective with the given name is found.
        """
        return self.adjectives[name]

    def add_explanation_tactics_to_adjective(self, to_adjective: str, tactics: List['Tactic']) -> None:
        """
        Add explanation tactics to a specified adjective.

        :param to_adjective: The name of the adjective to add tactics to.
        :param tactics: A list of :class:`Tactic` objects to add.
        """
        tactic_tuples = [(tactic, to_adjective) for tactic in tactics]
        self.add_explanation_tactics(tactic_tuples)
    
    def add_explanation_tactics(self, tactics: List[Union['Tactic', Tuple['Tactic', str]]]) -> None:
        """
        Add explanation tactics from a list of tactics or tuple of tactic and adjective for specific adjectives' tactics.

        :param tactics: A list of :class:`Tactic` objects or tuples of (:class:`Tactic`, str).
        """
        for tactic_input in tactics:
            if isinstance(tactic_input, tuple):
                tactic, to_adjective = tactic_input
                self.add_explanation_tactic(tactic, to_adjective=to_adjective)
            else:
                self.add_explanation_tactic(tactic_input)
    
    def add_explanation_tactic(self, tactic: 'Tactic', *, to_adjective: str = '') -> None:
        """
        Add an explanation tactic to the framework or a specific adjective.

        :param tactic: The :class:`Tactic` object to add.
        :param to_adjective: The name of the adjective to add the tactic to (if any).
        """
        if to_adjective:
            adjective = self.get_adjective(to_adjective)
            adjective.add_explanation_tactic(tactic)
            return

        tactics_to_add = [tactic] + tactic.get_requirements()
        self._add_explanation_tactics(tactics_to_add)
            
    def del_explanation_tactic(self, tactic_class_name: str, *, to_adjective: str = '') -> None:
        """
        Delete an explanation tactic from the framework or a specific adjective.

        :param tactic_class_name: The name of the tactic class to delete.
        :param to_adjective: The name of the adjective to delete the tactic from (if any).
        """
        if to_adjective:
            adjective = self.get_adjective(to_adjective)
            tactic = adjective.get_explanation_tactic(tactic_class_name)
        else:
            tactic = self.get_explanation_tactic(tactic_class_name)

        tactics_to_delete_names = [tactic_class_name] + [req.name for req in tactic.requirements]

        if to_adjective:
            adjective._del_explanation_tactics(tactics_to_delete_names)
        else:
            self._del_explanation_tactics(tactics_to_delete_names)

    def _add_explanation_tactics(self, tactics: List['Tactic']) -> None:
        """
        Add multiple explanation tactics to the framework.

        :param tactics: A list of :class:`Tactic` objects to add.
        """
        for tactic in tactics:
            tactic.contextualize(self)
            self.general_explanation_tactics[tactic.name] = tactic
    
    def _del_explanation_tactics(self, tactic_names: List[str]) -> None:
        """
        Delete multiple explanation tactics from the framework.

        :param tactic_names: A list of tactic names to delete.
        """
        for tactic_name in tactic_names:
            del self.general_explanation_tactics[tactic_name]

    def get_explanation_tactic(self, tactic_name: str) -> 'Tactic':
        """
        Retrieve an explanation tactic from the framework.

        :param tactic_name: The name of the tactic to retrieve.
        :return: The :class:`Tactic` object with the given name.
        :raises KeyError: If no tactic with the given name is found.
        """
        return self.general_explanation_tactics[tactic_name]
    
    def __str__(self) -> str:
        """
        Return a string representation of the ArgumentationFramework.

        :return: A string containing the propositions of all adjectives in the framework.
        """
        propositions = [str(adjective.proposition()) for adjective in self.adjectives.values()]
        framework_string = 'Propositions:\n' + '\n'.join(propositions)
        return framework_string