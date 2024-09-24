Explanations
=================================
Explanations are the base of inference for an adjective to be assigned.
Why is a node leaf?
Why is a node's score = 4?
Why is a node better than another?

All Explanations redirect to underlying explanations because they refer to other adjectives.
Only Assumptions don't, stopping the explanation inception.

Assumptions
-----------

.. autoclass:: src.explainer.explanations.assumption.Assumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.assumption.PossessionAssumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.assumption.ComparisonAssumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.assumption.RankAssumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

Fundamental Explanations
-------------------

.. autoclass:: src.explainer.explanations.fundamental_explanation.Possession
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.fundamental_explanation.Comparison
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.fundamental_explanation.ComparisonNodesPropertyPossession
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.fundamental_explanation.GroupComparison
    :members: __init__
    :undoc-members:
    :show-inheritance:

Composite Explanations
----------------------

.. autoclass:: src.explainer.explanations.composite_explanation.CompositeExplanation
    :members: __init__
    :undoc-members:
    :show-inheritance:

Conditional Explanations
------------------------

.. autoclass:: src.explainer.explanations.conditional_explanation.If
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.conditional_explanation.ConditionalExplanation
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanations.conditional_explanation.RecursivePossession
    :members: __init__
    :undoc-members:
    :show-inheritance:

Main Explanation Class (internal use only)
------------------------------------------

.. autoclass:: src.explainer.explanations.base.Explanation
    :members: __init__
    :undoc-members:
    :show-inheritance: