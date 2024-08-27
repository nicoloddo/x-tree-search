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

from .explanations.simple_explanations import Assumption, PossessionAssumption, ComparisonAssumption, RankAssumption, Possession, Comparison, ComparisonNodesPropertyPossession, GroupComparison, CompositeExplanation
__all__.extend(['Assumption', 'PossessionAssumption', 'ComparisonAssumption', 'RankAssumption', 'Possession', 'Comparison', 'ComparisonNodesPropertyPossession', 'GroupComparison', 'CompositeExplanation'])

from .explanations.conditional_explanation import If, ConditionalExplanation
__all__.extend(['If', 'ConditionalExplanation'])