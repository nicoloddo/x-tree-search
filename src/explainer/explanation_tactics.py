from abc import ABC, abstractmethod

from src.explainer.adjective import MaxRankAdjective, MinRankAdjective, NodesGroupPointerAdjective

class Tactic(ABC):
    """Abstract base class for all types of explanation tactics.
    Explanation tactics affect how adjective evaluate(), proposition() and explain(),
    the latter by affecting also Explanation.explain().
    Each tactic affects specific Adjectives and Explanations and you can find how they
    are affected by searching for the tactics if inside the Adjective or Explanation.
    
    The methods of apply need to directly modify the arguments, not return."""
    def __init__(self, name):
        self.name = name
        self.framework = None
        self.tactic_of_adjective = None

    def set_belonging_framework(self, framework):
        self.framework = framework

    def contextualize(self, adjective: 'Adjective'):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.tactic_of_adjective = adjective
        self.framework = adjective.framework
        self._contextualize()
        
        self.validate_context()
    
    @property
    @abstractmethod
    def allowed_attached_to_adjectives(self):
        pass

    def validate_context(self):
        for allowed_adjective in self.allowed_attached_to_adjectives:
            if isinstance(self.tactic_of_adjective, allowed_adjective):
                return True        
        raise ValueError(f"{self.__class__.__name__} can only be ATTACHED to adjectives among {self.allowed_attached_to_adjectives}.")
    
    def _contextualize(self, *args, **kwargs):
        pass

    def apply(self, scope, calling_adjective, *args, **kwargs) -> None:
        if not self.validate_apply(calling_adjective):
            return

        allowed_scopes = ["proposition", "evaluation", "explanation"]
        if scope not in allowed_scopes:
            raise ValueError("The scope of application of a tactic must be among " + str(allowed_scopes))
        
        if scope == "proposition":
            self.apply_on_proposition(*args, **kwargs)
        elif scope == "evaluation":
            self.apply_on_evaluation(*args, **kwargs)
        elif scope == "explanation":
            self.apply_on_explanation(*args, **kwargs)
        else:
            raise ValueError(f"Something went wrong when selecting the {self.name} tactic's scope.")
    
    @property
    @abstractmethod
    def allowed_applied_to_adjectives(self):
        pass

    def validate_apply(self, calling_adjective):
        for allowed_adjective in self.allowed_applied_to_adjectives:
            if isinstance(calling_adjective, allowed_adjective):
                return True
        return False  
        #raise ValueError(f"{self.__class__.__name__} can only be APPLIED to adjectives among {self.allowed_applied_to_adjectives}.")

class OnlyRelevantComparisons(Tactic):
    """When explaining a GroupComparison, only explain
    the comparison between relevant objects."""
    top_n = 'err' # we set to 'err' because with None, sorted() would still work.
    bottom_n = 'err'
    show_n = 'err'
    eval_tactic = None
    
    def __init__(self, *, mode: str):
        super().__init__(self.__class__.__name__)
        self.mode = mode
        self.set_mode()

    def set_mode(self):
        if self.mode.startswith("top_"):
            characters_before_n = len("top_")
            self.show_n = self.mode[characters_before_n:]
            n = int(self.show_n)
            if self.show_n.isdigit() and n > 0:
                self.top_n = n
            else:
                raise ValueError("A top_n mode should have an integer greater than 0.")
            
            self.eval_tactic = self.relevant_top_n
            
        elif self.mode.startswith("bottom_"):
            characters_before_n = len("bottom_")
            self.show_n = self.mode[characters_before_n:]
            n = int(self.show_n)
            if self.show_n.isdigit() and n > 0:
                self.bottom_n = n
            else:
                raise ValueError("A bottom_n mode should have an integer greater than 0.")
            
            self.eval_tactic = self.relevant_bottom_n

    @property
    def allowed_attached_to_adjectives(self):
        return [MaxRankAdjective, MinRankAdjective]
    
    @property
    def allowed_applied_to_adjectives(self):
        return [NodesGroupPointerAdjective]

    def apply_on_proposition(self, proposition):
        proposition.expr += f" (only showing relevant {self.show_n})"

    def apply_on_evaluation(self, group):
        comparison_adjective_name = self.tactic_of_adjective.comparison_adjective_name
        comparison_adjective = self.framework.get_adjective(comparison_adjective_name)
        value_for_comparison_adjective = self.framework.get_adjective(comparison_adjective.property_pointer_adjective_name)

        group[:] = self.eval_tactic(group, value_for_comparison_adjective) # slice assignment to modify in place the group
        
    def relevant_top_n(self, group, value_for_comparison_adjective):
        return sorted(group, key=lambda obj: value_for_comparison_adjective.evaluate(obj), reverse=True)[:self.top_n]
    
    def relevant_bottom_n(self, group, value_for_comparison_adjective):
        return sorted(group, key=lambda obj: value_for_comparison_adjective.evaluate(obj), reverse=False)[:self.bottom_n]