from abc import ABC, abstractmethod
from typing import Any, List
from src.explainer.common.utils import return_arguments

from src.explainer.propositional_logic import Implies, And

from src.explainer.adjective import Adjective
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import MaxRankAdjective, MinRankAdjective, NodesGroupPointerAdjective
from src.explainer.adjective import QuantitativePointerAdjective
from src.explainer.explanation import ConditionalExplanation

class Tactic(ABC):
    """Abstract base class for all types of explanation tactics.
    Explanation tactics affect how adjective evaluate(), proposition() and explain(),
    the latter by affecting also Explanation.explain().
    Each tactic can affect specific Adjectives and Explanations or the whole Framework.

    Tactics are called from adjectives during their explanation."""

    def __init__(self, name, use_on_adjectives = []):
        """
        The tactic name will automatically be assigned by children classes.

        The use_on_adjectives can be specified through the init of children classes
        and should include names of adjectives from which the tactic can be executed.
        If the use_on_adjectives is not specified, any adjective name will be allowed.
        """
        self.name = name
        self.use_on_adjectives = use_on_adjectives
        self.framework = None
        self.tactic_of_object = None

    def set_belonging_framework(self, framework):
        self.framework = framework

    @abstractmethod
    def contextualize(self, belonging_object: 'Adjective'):
        """Sets the Argumentation framework the Explanation belongs to."""
        pass

    @abstractmethod
    def validate_context(self):
        pass

    @property
    # List of adjective types from which the tactic is performed.
    # Do not override if you want to be able to use this tactic from
    # any type of adjective (or return an empty array). 
    # Override in any other occasion.
    # Examples below.
    def exec_from_adjective_types(self) -> List:
        return []
    
    @property
    # List of explanation types onto which the tactic can be applied.
    # Do not override if you want to be able to use this tactic on
    # any type of explanation (or return an empty array). 
    # Override in any other occasion.
    # Examples below.
    def allowed_on_explanation_types(self) -> List:
        return []

    def validate_apply(self, calling_adjective):
        allowed_adjective_type = False
        allowed_adjective = False
        allowed_explanation_type = False

        if len(self.exec_from_adjective_types) == 0:
            allowed_adjective_type = True
        else:
            for allowed_type in self.exec_from_adjective_types:
                if isinstance(calling_adjective, allowed_type):
                    allowed_adjective_type = True
        
        if len(self.use_on_adjectives) == 0:
            allowed_adjective = True
        else:
            for allowed in self.use_on_adjectives:
                if isinstance(calling_adjective.name, allowed):
                    allowed_adjective = True

        if len(self.allowed_on_explanation_types) == 0:
            allowed_explanation_type = True
        else:
            for allowed_type in self.allowed_on_explanation_types:
                if isinstance(calling_adjective.explanation, allowed_type):
                    allowed_explanation_type = True
        
        return allowed_adjective_type and allowed_explanation_type and allowed_adjective
    

    def apply(self, calling_adjective, scope, *args) -> Any:
        if all(arg is None for arg in args):
            return return_arguments(*args)

        if not self.validate_apply(calling_adjective):
            return return_arguments(*args)

        allowed_scopes = ["proposition", "evaluation", "explanation"]
        if scope not in allowed_scopes:
            raise ValueError("The scope of application of a tactic must be among " + str(allowed_scopes))
        
        if scope == "proposition":
            result = self.apply_on_proposition(*args)
        elif scope == "evaluation":
            result = self.apply_on_evaluation(*args)
        elif scope == "explanation":
            result = self.apply_on_explanation(*args)
        else:
            raise ValueError(f"Something went wrong when selecting the {self.name} tactic's scope.")

        return result
    
    # Apply functions 
    # Override if you want the tactic to be used
    def apply_on_proposition(self, proposition):
        return proposition 

    def apply_on_evaluation(self, evaluation):
        return evaluation

    def apply_on_explanation(self, explanation):
        return explanation

class SpecificTactic(Tactic):
    """Specific Tactics are allowed to start only from a selected adjective explanation."""
    @property
    @abstractmethod
    def allowed_in_expl_starting_from_adjective_types(self) -> List:
    # List of adjective types from which explanation the tactic will be applied.
    # The tactic will be applied only if the explanation is starting from one of those.
    # Examples below.
        pass

    def contextualize(self, adjective: Adjective):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.tactic_of_object = adjective
        self.tactic_of_adjective = adjective
        self.framework = adjective.framework        
        self.validate_context()

    def validate_context(self):
        for allowed_adjective in self.allowed_in_expl_starting_from_adjective_types:
            if isinstance(self.tactic_of_adjective, allowed_adjective):
                return True        
        raise ValueError(f"{self.__class__.__name__} can only be ATTACHED to adjectives among {self.allowed_in_expl_starting_from_adjective_types}.")
    
class GeneralTactic(Tactic):
    """General Tactics are allowed to start from any adjective explanation."""
    @property
    def allowed_in_expl_starting_from_adjective_types(self) -> List:
    # List of adjectives to which explanation the tactic will be applied from.
        return [] # It will not be used as we override validate_context
    
    def contextualize(self, framework: ArgumentationFramework):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.tactic_of_object = framework
        self.tactic_of_framework = framework
        self.framework = framework
        
        self.validate_context()
    
    def validate_context(self):
        if isinstance(self.tactic_of_object, ArgumentationFramework):
            return True
        raise ValueError(f"{self.__class__.__name__} can only be ATTACHED to a whole framework. Do not specify an adjective.")
    
class OnlyRelevantComparisons(SpecificTactic):
    """When explaining a GroupComparison, only explain
    the comparison between relevant objects."""
    top_n = 'err' # we set to 'err' because with None, sorted() would still work.
    bottom_n = 'err'
    show_n = 'err'
    eval_tactic = None
    
    @property
    def allowed_in_expl_starting_from_adjective_types(self):
        return [MaxRankAdjective, MinRankAdjective]
    
    @property
    def exec_from_adjective_types(self):
        return [NodesGroupPointerAdjective]
    
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
    
    def relevant_top_n(self, group, value_for_comparison_adjective):
        return sorted(group, key=lambda obj: value_for_comparison_adjective.evaluate(obj), reverse=True)[:self.top_n]
    
    def relevant_bottom_n(self, group, value_for_comparison_adjective):
        return sorted(group, key=lambda obj: value_for_comparison_adjective.evaluate(obj), reverse=False)[:self.bottom_n]

    # apply
    def apply_on_proposition(self, proposition):
        proposition.expr += f" (only showing relevant {self.show_n})"
        return proposition

    def apply_on_evaluation(self, group):
        comparison_adjective_name = self.tactic_of_adjective.comparison_adjective_name
        comparison_adjective = self.framework.get_adjective(comparison_adjective_name)
        value_for_comparison_adjective = self.framework.get_adjective(comparison_adjective.property_pointer_adjective_name)

        group = self.eval_tactic(group, value_for_comparison_adjective)
        return group
    
class SkipQuantitativeExplanations(GeneralTactic):
    """When explaining a QuantitativePointerAdjective, skip its statement
    and pass directly to the explanation of the PointerAdjective instead."""
    
    @property
    def exec_from_adjective_types(self):
        return [QuantitativePointerAdjective]

    def __init__(self):
        super().__init__(self.__class__.__name__)

    # apply    
    def apply_on_explanation(self, explanation):
        if isinstance(explanation, Implies):
            return explanation.antecedent
        else:
            return None
        
class SkipConditionStatement(GeneralTactic):
    """When explaining a QuantitativePointerAdjective, skip its statement
    and pass directly to the explanation of the PointerAdjective instead."""

    @property
    def allowed_on_explanation_types(self) -> List:
        return [ConditionalExplanation]

    def __init__(self, *, use_on_adjectives: List = []):
        """Leave use_on_adjectives blank if you want to use it on all adjectives."""
        super().__init__(self.__class__.__name__, use_on_adjectives)

    # apply    
    def apply_on_explanation(self, explanation):
        if isinstance(explanation, Implies):
            antecedent = explanation.antecedent
            antecedent.exprs = tuple(antecedent.exprs[1:]) # The first expression is the condition statement.
            return explanation
        elif isinstance(explanation, And): 
            # we already have the antecedent, in occasions for example in which the consequent was cutted off
            # e.g. quantitative explanation with skipping tactic
            antecedent = explanation
            antecedent.exprs = tuple(antecedent.exprs[1:]) # The first expression is the condition statement.
            return explanation
        else:
            raise ValueError("Something went wrong with the SkipConditionStatement tactic: the explanation antecedent (ConditionalExplanation) should be an And expression but it is not.")