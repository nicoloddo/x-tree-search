from abc import ABC, abstractmethod
from typing import Any, List, Callable
from collections import defaultdict

from src.explainer.common.utils import return_arguments

from src.explainer.propositional_logic import Postulate, NAryOperator, Implies, And, Proposition

from src.explainer.adjective import Adjective
from src.explainer.framework import ArgumentationFramework

from src.explainer.adjective import MaxRankAdjective, MinRankAdjective, NodesGroupPointerAdjective
from src.explainer.adjective import QuantitativePointerAdjective
from src.explainer.adjective import ComparisonAdjective

from src.explainer.explanation import Possession, RecursivePossession

class Tactic(ABC):
    """Abstract base class for all types of explanation tactics.
    Explanation tactics affect how adjective evaluate(), proposition() and explain(),
    the latter by affecting also Explanation.explain().
    Each tactic can affect specific Adjectives and Explanations or the whole Framework.

    Tactics are called from adjectives during their explanation.""" 

    def __init__(self, name, *, use_on_adjectives: List[str] = [], except_on_adjectives: List[str] = []):
        """
        The tactic name will automatically be assigned by children classes.

        The use_on_adjectives can be specified through the init of children classes
        and should include names of adjectives from which the tactic can be executed.
        If the use_on_adjectives is not specified, any adjective name will be allowed.
        """
        self.name = name
        self.use_on_adjectives = use_on_adjectives
        self.except_on_adjectives = except_on_adjectives
        self.framework = None
        self.tactic_of_object = None

        """Requirements are a list of other tactics instantiations that are required for one tactic to work.
        Add them during the __init__ by calling the required tactic constructor.
        You should append a list with the class as first item and the args as second in a tuple.
        e.g. self.requirements.append([Tactic, (mode)])
        An example can be found at SubstituteQuantitativeExplanations."""
        self.requirements = []

    @abstractmethod
    def contextualize(self, belonging_object: 'Adjective'):
        """Sets the object and the framework the Explanation belongs to."""
        pass

    @abstractmethod
    def decontextualize(self):
        """Undo the contextualization."""
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
    
    all_possible_explanation_parts = ['whole', 'consequent'] 
    @property
    # List of explanation parts onto which the tactic can be applied.
    # Do not override if you want to be able to constrain this tactic
    # to specific parst of the explanation (or return an empty array).
    # Allowed parts are: whole, antecedent, consequent. 
    # Override in any other occasion.
    # Examples below.
    def allowed_on_explanation_parts(self) -> List:
        return self.all_possible_explanation_parts

    def validate_apply(self, calling_adjective, scope, explanation_part):
        allowed_explanation_part = True if scope != 'explanation' else False 
        # No need to check explanation part if the scope is not explanation

        allowed_adjective_type = False
        allowed_adjective = False
        allowed_explanation_type = False

        if scope=='explanation' and explanation_part in self.allowed_on_explanation_parts:
            allowed_explanation_part = True

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
                if calling_adjective.name == allowed:
                    allowed_adjective = True
        for not_allowed in self.except_on_adjectives:
            if calling_adjective.name == not_allowed:
                allowed_adjective = False

        if len(self.allowed_on_explanation_types) == 0:
            allowed_explanation_type = True
        else:
            for allowed_type in self.allowed_on_explanation_types:
                if isinstance(calling_adjective.explanation, allowed_type):
                    allowed_explanation_type = True
        
        return allowed_explanation_part and allowed_adjective_type and allowed_explanation_type and allowed_adjective
    

    def apply(self, calling_adjective, scope, explanation_part, *args) -> Any:
        if all(arg is None for arg in args):
            return return_arguments(*args)

        if not self.validate_apply(calling_adjective, scope, explanation_part):
            return return_arguments(*args)

        allowed_scopes = ["proposition", "evaluation", "explanation"]
        if scope not in allowed_scopes:
            raise ValueError("The scope of application of a tactic must be among " + str(allowed_scopes))

        if scope == 'explanation' and explanation_part not in self.all_possible_explanation_parts:
            raise ValueError("The explanation part of application of a tactic must be among " + str(self.all_possible_explanation_parts))
        
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
    
    def get_requirements(self):
        recursive_requirements = []
        for requirement in self.requirements:
            requirement_tactic = requirement[0](*requirement[1])
            recursive_requirements.append(requirement_tactic)
            recursive_requirements += requirement_tactic.get_requirements()
        return recursive_requirements

class SpecificTactic(Tactic):
    """Specific Tactics are allowed to start only from a selected adjective explanation."""
    @property
    @abstractmethod
    def allowed_in_expl_starting_from_adjective_types(self) -> List:
    # List of adjective types from which explanation the tactic will be applied.
    # The tactic will be applied only if the explanation is starting from one of those.
    # Leave empty if you want to allow it from any adjective type.
        pass

    def contextualize(self, adjective: Adjective):
        """Sets the Argumentation framework the Explanation belongs to."""
        self.tactic_of_object = adjective
        self.tactic_of_adjective = adjective
        self.framework = adjective.framework        
        self.validate_context()
    
    def decontextualize(self):
        self.tactic_of_object = None
        self.tactic_of_framework = None
        self.framework = None

    def validate_context(self):
        if len(self.allowed_in_expl_starting_from_adjective_types) == 0:
            return True
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

    def decontextualize(self):
        self.tactic_of_object = None
        self.tactic_of_framework = None
        self.framework = None
    
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
        proposition.add_info(f"only showing relevant {self.show_n}")
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

class SubstituteQuantitativeExplanations(GeneralTactic):
    """When explaining a QuantitativePointerAdjective, skip its statement
    and pass directly to the explanation of the PointerAdjective instead.
    It has as dependency the SkipQuantitativeExplanation tactic.
    This version of the tactic can only be applied generally, it would not
    work as a Specific Tactic because it relies on the SkipQuantitativeExplanation
    to delete the quantitative explanations."""
    
    @property
    def exec_from_adjective_types(self):
        return [ComparisonAdjective]

    def __init__(self, substitution_statement):        
        self.substitution_statement = Postulate('\t' + substitution_statement)
        super().__init__(self.__class__.__name__)

        self.requirements.append([SkipQuantitativeExplanations, ()])

    # apply    
    def apply_on_explanation(self, explanation):
        if isinstance(explanation, Implies):
            explanation.antecedent = Implies(explanation.antecedent, self.substitution_statement)
        
        return explanation
    

class CompactSameExplanations(SpecificTactic):
    """When explaining a Comparison, compact
    explanations that has to a similar explanation."""
    
    def __init__(self, *, from_adjectives: List[str], same_if_equal_keys = List, relevant_predicate_inside_list: int = -1, same_evaluation: Callable = None):
        """
        Build the CompactSameExplanations tactic.

        Note: the tactic will not compact Recursive Possessions.

        The tactic takes each explanation part of the adjective it was attached to (the explanation needs to be composite for this
        to make sense applying), and it checks if those parts have analogous explanations that could be compacted.
        To do so, you specify the adjectives which explanations might be analogous across the main adjective's explanation parts,
        and important characteristics of the adjective, which the similarity will be based from.
        You can specify a same_evaluation method that checks for similarity between the adjective's evaluation, in case it is needed
        a more complex similarity check.

        Parameters:
        - from_adjectives (list of str): The adjectives which explanations should be checked for similarity.
        - same_if_equal_keys (list): A list where each element can be:
            - A string representing the key to be checked for equality (e.g., 'depth').
            - A tuple where the first element is a key (str) and the second element is 
            the list of attributes to be checked. All must be the same for two explanations to be recognized as the same.
            
            For now supported keys are:
            'depth', 'explanation_type' and 'evaluation', 
            the latter being the most important feature this tactic was created for.
            Depth is by default inserted, meaning that only explanation at the same explanation depth will be considered for compacting.

        - relevant_predicate_inside_list (int) Default -1: If the predicates in the explanation are multiple,
            use this index to select the most relevant predicate among them. As default, we use the last predicate.
            e.g. If "next move" is present multiple times in a single explanation part, which one should we consider for the comparisons?
        - same_evaluation (callable, 2 args): Function that accepts (evaluation1, evaluation2) and returns a bool reflecting if the two are
            to be recognized as the same evaluation. Leave blank if you can achieve this through checking keys. 
            Adding this check slows down the application. 
        """
        super().__init__(self.__class__.__name__)
        self.from_adjectives = from_adjectives

        self.allowed_keys_to_check = ['depth', 'evaluation']

        default_same_if_equal_keys = ['depth']
        self.same_if_equal_keys = default_same_if_equal_keys + same_if_equal_keys

        self.relevant_predicate_inside_list = relevant_predicate_inside_list
        self.same_evaluation = same_evaluation
    
    def build_key(self, expl, most_relevant_predicate_index):
        """
        Build a key based on the given same_if_equal_keys definition.

        Parameters:
        - expl (dict): The dictionary containing the data.
        - most_relevant_predicate_index (int): The index to use for retrieving values from `expl`.
        
        Returns:
        - tuple: A tuple representing the key built from the provided definitions.
        """
        key = []
        
        for key_def in self.same_if_equal_keys:
            # Handle the case where key_def is a string (e.g., 'depth')
            if isinstance(key_def, str):
                key_name = key_def
                attributes = None
            else:
                key_name = key_def[0]
                attributes = key_def[1] if len(key_def) > 1 else None
            
            if key_name not in self.allowed_keys_to_check:
                raise SyntaxError(f"{key_name} is not an allowed key to check to CompactSameExplanations.")
            
            # Access the key in the expl dictionary
            value = expl[key_name][most_relevant_predicate_index]
            
            # If attributes are provided, access them one by one
            if attributes:
                # Append multiple attributes if they are provided
                for attr in attributes:
                    key.append(getattr(value, attr))
            else:
                # If no attributes, append the value directly
                key.append(value)
        
        return tuple(key)
    
    @property
    def allowed_in_expl_starting_from_adjective_types(self):
        return [MaxRankAdjective, MinRankAdjective]
    
    @property
    def exec_from_adjective_types(self):
        return [ComparisonAdjective]
    
    def apply_on_explanation(self, explanation):
        if not isinstance(explanation, Implies):
            return explanation

        # If the antecedent is not an And, there is nothing to compact (that's not a composite explanation)
        if not isinstance(explanation.antecedent, And):
            return explanation
        
        explanations_book = []
        # We need to unify similar exprs of the antecedent:
        for explanation_part in explanation.antecedent.exprs:

            # Get explanation types and subexpressions
            explanation_part_type = explanation_part.record['explanation_type']

            # Start with the explanation part itself
            explanation_types = [explanation_part_type]
            sub_exprs = [explanation_part]
            
            if isinstance(explanation_part, NAryOperator):
                explanation_types.extend([e.record['explanation_type'] for e in explanation_part.exprs])
                sub_exprs.extend(explanation_part.get_flat_exprs(max_depth=2)) # go down to explanation_part.exprs.exprs and add them
            
            explanations_book.append({'explanation_part_type': explanation_part_type,
                                      'subexpression': sub_exprs,
                                      # Keys of subexpressions:
                                      'explanation_type': explanation_types, # explanation_types of subexpressions
                                      'predicate': [expr.predicate for expr in sub_exprs],
                                      'evaluation': [expr.evaluation for expr in sub_exprs],
                                      'depth': [expr.record['depth'] for expr in sub_exprs],
                                      'record': [expr.record for expr in sub_exprs]})
        
        # Delete already seen similar instances
        def compact_and_delete(current, seen, explanation_part_to_nullify_index):
            # We get the subjects to add to the instance seen before
            subjects_to_add = current.subject
            if not isinstance(subjects_to_add, list):
                subjects_to_add = [subjects_to_add]

            # We add the subjects to the previously seen instance
            if not isinstance(seen.subject, list):
                seen.subject = [seen.subject]
            seen.subject.extend(subjects_to_add)
            
            # We nullify explanation for this occurrence
            explanation.antecedent.exprs[explanation_part_to_nullify_index].nullify()

        seen = {}
        most_relevant_predicate_indexes = []
        for i, expl in enumerate(explanations_book):
            if len(expl['subexpression']) == 0:
                continue

            if RecursivePossession in expl['explanation_type']: # We do not compact Recursive Possessions
                continue

            relevant_predicates_indexes = [p for p, predicate in enumerate(expl['predicate']) if predicate in self.from_adjectives]
            if len(relevant_predicates_indexes) == 0: # No predicates found from the given adjectives 
                continue
            
            # Select the most relevant predicate by getting its index among subexpressions. 
            # By default we consider the last predicate as the most relevant.
            most_relevant_predicate_index = relevant_predicates_indexes[self.relevant_predicate_inside_list]
            most_relevant_predicate_indexes.append(most_relevant_predicate_index)
            most_relevant_subexpression = expl['subexpression'][most_relevant_predicate_index]

            key = self.build_key(expl, most_relevant_predicate_index)
            
            if key not in seen:
                # This key was never seen before
                
                if self.same_evaluation is not None: 
                    # The key was not seen before, but it could still be the same 
                    # because of the more complex same_evaluation assessment
                    current_evaluation = expl['evaluation'][most_relevant_predicate_index]

                    # Iterate through previous explanations until the current one
                    for j in range(i):
                        previous_relevant_predicate_index = most_relevant_predicate_indexes[j]
                        previous_evaluation = explanations_book[j]['evaluation'][previous_relevant_predicate_index]
                        previous_relevant_subexpression = explanations_book[j]['subexpression'][previous_relevant_predicate_index]
                        
                        # Compare evaluations using the provided function
                        if self.same_evaluation(current_evaluation, previous_evaluation):
                            compact_and_delete(most_relevant_subexpression, previous_relevant_subexpression, i)
                            break
                    else:
                        # Was definitely not seen, we add it to the seen
                        seen[key] = most_relevant_subexpression
                else:
                    # The key was not seen before and there is no further check to do
                    seen[key] = most_relevant_subexpression

            else:
                # Item is similar to one already seen (has the same key)
                compact_and_delete(most_relevant_subexpression, seen[key], i)

        return explanation