ArgumentationFramework
======================

.. currentmodule:: src.explainer

.. autoclass:: ArgumentationFramework

The ``ArgumentationFramework`` class is a central component for managing adjectives and their relationships in an argumentation system. It provides functionality to add, remove, and manage adjectives, as well as explanation tactics for the framework.

Main Usage
----------

The primary way to use the ``ArgumentationFramework`` class is to create an instance with the necessary parameters to be attached to an :class:`ArgumentativeExplainer`:

.. code-block:: python

    # Create argumentation framework
    highlevel_framework = ArgumentationFramework(
        refer_to_nodes_as='move',
        adjectives=adjectives,
        tactics=tactics,
        settings=settings,
    )

- ``refer_to_nodes_as``: Specifies how to refer to nodes when printing explanations (e.g., 'move', 'position', 'node').
- ``adjectives``: A list of :class:`Adjective` objects to be added to the framework.
- ``tactics``: A list of explanation tactics (either :class:`Tactic` objects or tuples of (:class:`Tactic`, str name of adjective to apply it to)) for the framework.
- ``settings``: A dictionary of framework-specific settings.

Settings
-------------------

.. autoclass:: ExplanationSettings

Example of settings:

.. code-block:: python

    settings = {
        'explanation_depth': 4,
        'print_implicit_assumptions': False,
        'assumptions_verbosity': 'verbose',
        'print_mode': 'verbal',
    }

Internal Methods
----------------

While the main usage is straightforward, the ``ArgumentationFramework`` class provides various internal methods for managing adjectives, tactics, and settings:

Adjective Management
^^^^^^^^^^^^^^^^^^^^

.. automethod:: ArgumentationFramework.add_adjective
.. automethod:: ArgumentationFramework.del_adjective
.. automethod:: ArgumentationFramework.has_adjective
.. automethod:: ArgumentationFramework.add_adjectives
.. automethod:: ArgumentationFramework.rename_adjective
.. automethod:: ArgumentationFramework.get_adjective

These methods allow for adding, removing, checking, and retrieving adjectives within the framework.

Explanation Tactics
^^^^^^^^^^^^^^^^^^^

.. automethod:: ArgumentationFramework.add_explanation_tactics_to_adjective
.. automethod:: ArgumentationFramework.add_explanation_tactics
.. automethod:: ArgumentationFramework.add_explanation_tactic
.. automethod:: ArgumentationFramework.del_explanation_tactic
.. automethod:: ArgumentationFramework.get_explanation_tactic

These methods provide functionality for managing explanation tactics, both general and adjective-specific.

Settings Management
^^^^^^^^^^^^^^^^^^^

.. automethod:: ArgumentationFramework.set_settings
.. automethod:: ArgumentationFramework.actuate_settings

These methods handle the framework-specific settings.

Additional Methods
^^^^^^^^^^^^^^^^^^

.. automethod:: ArgumentationFramework.__str__

This method provides a string representation of the framework, listing all adjective propositions.

Attributes
----------

- ``tree_search_motivation``: A string describing the motivation for tree search.
- ``refer_to_nodes_as``: How to refer to nodes when printing explanations.
- ``adjectives``: A dictionary of :class:`Adjective` objects in the framework.
- ``general_explanation_tactics``: A dictionary of general explanation tactics.
- ``settings``: An :class:`ExplanationSettings` object for framework-specific settings.
- ``framework_specific_settings``: A boolean indicating if framework-specific settings are used.