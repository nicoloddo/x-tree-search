Explanations
=================================
Explanations are the base of inference for an adjective to be assigned.
Why is a node leaf?
Why is a node's score = 4?
Why is a node better than another?

All Explanations redirect to underlying explanations because they refer to other adjectives.
Only Assumptions don't, stopping the explanation inception.
When giving an explanation, think of explanation classes as providing a statement like:
"because the node possesses this score"
or 
"because the node is a leaf"
Assumptions
-----------

.. autoclass:: src.explainer.explanation.Assumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.PossessionAssumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.ComparisonAssumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.RankAssumption
    :members: __init__
    :undoc-members:
    :show-inheritance:

Fundamental Explanations
-------------------

.. autoclass:: src.explainer.explanation.Possession
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.Comparison
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.ComparisonNodesPropertyPossession
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.GroupComparison
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.RecursivePossession
    :members: __init__
    :undoc-members:
    :show-inheritance:

Composite Explanations
----------------------

.. autoclass:: src.explainer.explanation.CompositeExplanation
    :members: __init__
    :undoc-members:
    :show-inheritance:

Conditional Explanations
------------------------

.. autoclass:: src.explainer.explanation.If
    :members: __init__
    :undoc-members:
    :show-inheritance:

.. autoclass:: src.explainer.explanation.ConditionalExplanation
    :members: __init__
    :undoc-members:
    :show-inheritance:

Main Explanation Class (internal use only)
------------------------------------------

.. autoclass:: src.explainer.explanation.Explanation
    :members: __init__
    :undoc-members:
    :show-inheritance: