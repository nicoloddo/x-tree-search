from typing import Any, Dict

from src.explainer.adjective import Adjective, StaticAdjective, PointerAdjective, RankingAdjective
from src.explainer.explanation import AssumptionExplanation, SiblingsComparisonExplanation, CompositeExplanation

MAX_RANKING_ASSUMPTION = AssumptionExplanation(
    "A node is max-ranked in a RankingAdjective if the Ranking Condition is TRUE when compared to all its siblings.")
MIN_RANKING_ASSUMPTION = AssumptionExplanation(
    "A node is min-ranked in a RankingAdjective if the Ranking Condition is FALSE when compared to all its siblings.")

class ArgumentationFramework:
    """Manages adjectives and their relationships in the argumentation framework."""
    
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
        if isinstance(adjective, RankingAdjective):
            self._create_max_min_adjectives(adjective)

    def _create_max_min_adjectives(self, ranking_adjective: RankingAdjective):
        """
        Create max and min static adjectives from a ranking adjective.
        
        Args:
            ranking_adjective: The RankingAdjective to derive from.
        """
        sibling_selector = lambda node: [sibling for sibling in node.parent.children if sibling is not node]

        def max_condition(node: Any) -> bool:
            siblings = sibling_selector(node)
            return all(ranking_adjective.evaluate(node, sibling) for sibling in siblings)

        def min_condition(node: Any) -> bool:
            siblings = sibling_selector(node)
            return all(ranking_adjective.evaluate(sibling, node) for sibling in siblings)

        max_name = f"max_{ranking_adjective.name}"
        min_name = f"min_{ranking_adjective.name}"

        max_explanation = CompositeExplanation(
            MAX_RANKING_ASSUMPTION,
            SiblingsComparisonExplanation(ranking_adjective.name, sibling_selector))
        min_explanation = CompositeExplanation(
            MIN_RANKING_ASSUMPTION,
            SiblingsComparisonExplanation(ranking_adjective.name, sibling_selector))

        self.add_adjective(StaticAdjective(max_name, max_condition, max_explanation))
        self.add_adjective(StaticAdjective(min_name, min_condition, min_explanation))

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

    def get_adjective(self, name: str) -> Adjective:
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
