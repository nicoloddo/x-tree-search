"""
Explanations are the base of inference for an adjective to be assigned.
Why is a node leaf?
Why is a node's score = 4?
Why is a node better than another?

All Explanations redirect to underlying explanations.
Only Assumptions don't, stopping the explanation inception.
"""

from .explanations.base import Explanation
__all__ = ['Explanation']

from .explanations.assumption import Assumption, PossessionAssumption, ComparisonAssumption, RankAssumption
__all__.extend(['Assumption', 'PossessionAssumption', 'ComparisonAssumption', 'RankAssumption'])
                
from .explanations.fundamental_explanation import Possession, Comparison, ComparisonNodesPropertyPossession, GroupComparison, RecursivePossession
__all__.extend(['Possession', 'Comparison', 'ComparisonNodesPropertyPossession', 'GroupComparison', 'RecursivePossession'])

from .explanations.composite_explanation import CompositeExplanation
__all__.extend(['CompositeExplanation'])

from .explanations.conditional_explanation import If, ConditionalExplanation
__all__.extend(['If', 'ConditionalExplanation'])