from typing import Dict

from src.explainer.adjective import Adjective, StaticAdjective, PointerAdjective, PointerRankingAdjective
from src.explainer.explanation import Explanation

class ArgumentationFramework:
    """
    Class for managing adjectives, motivations, and explanations in the argumentation framework.
    This class handles the structure and relationships of adjectives and explanations.
    """
    def __init__(self):
        """Initialize the ArgumentationFramework."""
        self.adjectives: Dict[str, Adjective] = {}
        self.tree_search_motivation: str = ""

    def add_adjective(self, adjective: Adjective):
        """
        Add an adjective to the framework and create derived adjectives if it's a ranking adjective.

        Args:
            adjective: The Adjective object to add.
        """
        self.adjectives[adjective.name] = adjective
        if isinstance(adjective, PointerRankingAdjective):
            max_adjective = adjective.create_max_adjective()
            min_adjective = adjective.create_min_adjective()
            pointer_adjective = adjective.create_pointer_adjective()
            self.adjectives[max_adjective.name] = max_adjective
            self.adjectives[min_adjective.name] = min_adjective
            self.adjectives[pointer_adjective.name] = pointer_adjective

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

    def set_tree_search_motivation(self, adjective_name: str):
        """
        Set the adjective that motivates tree search choices.

        Args:
            adjective_name: The name of the adjective to use as motivation.

        Raises:
            ValueError: If no adjective with the given name is found.
        """
        if adjective_name not in self.adjectives:
            raise ValueError(f"Adjective '{adjective_name}' not found.")
        self.tree_search_motivation = adjective_name

    def set_adjective_explanation(self, adjective_name: str, explanation: Explanation):
        """
        Set or update the explanation for a specific adjective.

        Args:
            adjective_name: The name of the adjective to update.
            explanation: The new Explanation object for the adjective.

        Raises:
            ValueError: If no adjective with the given name is found.
        """
        if adjective_name not in self.adjectives:
            raise ValueError(f"Adjective '{adjective_name}' not found.")
        self.adjectives[adjective_name].explanation = explanation

    def get_adjective(self, adjective_name: str) -> Adjective:
        """
        Retrieve an adjective from the framework.

        Args:
            adjective_name: The name of the adjective to retrieve.

        Returns:
            The Adjective object with the given name.

        Raises:
            ValueError: If no adjective with the given name is found.
        """
        if adjective_name not in self.adjectives:
            raise ValueError(f"Adjective '{adjective_name}' not found.")
        return self.adjectives[adjective_name]