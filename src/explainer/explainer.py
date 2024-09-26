from typing import Any, Callable, Dict
from src.explainer.propositional_logic import Implies, Postulate
from src.explainer.explanation_settings import ExplanationSettings
from src.explainer.common.exceptions import CannotBeEvaluated

STARTING_EXPLANATION_DEPTH = 1

class ArgumentativeExplainer:
    """
    Generates explanations based on the argumentation framework.

    This class manages multiple argumentation frameworks and provides methods to
    generate explanations, evaluate nodes, and configure settings for the explanation process.

    It is recommended to provide a __str__(self) method in the node classes
    to ensure correct printing of the nodes.

    :ivar settings: The current explanation settings.
    :ivar framework: The currently selected argumentation framework.
    :ivar frameworks: A dictionary of available argumentation frameworks.
    :ivar getters: A dictionary of getter functions for adjectives.
    """

    def __init__(self):
        """
        Initialize the ArgumentativeExplainer.

        Sets up the initial state with empty frameworks and default settings.
        """
        self.settings: ExplanationSettings = ExplanationSettings()
        self.framework: 'ArgumentationFramework' = None
        self.frameworks: Dict[str, 'ArgumentationFramework'] = {}
        self.getters: Dict[str, Callable[[Any], Any]] = {}

    def add_framework(self, framework_name: str, framework: 'ArgumentationFramework'):
        """
        Add a framework to explain the tree search.

        :param framework_name: The name of the framework to add.
        :type framework_name: str
        :param framework: The argumentation framework to add.
        :type framework: ArgumentationFramework
        """
        self.frameworks[framework_name] = framework
        framework._set_settings(self.settings)

        if len(self.frameworks) == 1:
            # If this was the first added framework, select it automatically
            self.settings.with_framework = framework_name
            self.select_framework(framework_name)

    def select_framework(self, framework_name: str):
        """
        Selects the framework to use for the explanations.

        :param framework_name: The name of the framework to select.
        :type framework_name: str
        :raises KeyError: If the specified framework name is not found.
        """
        if framework_name not in self.frameworks:
            raise KeyError(f"Framework '{framework_name}' not found.")
        self.framework = self.frameworks[framework_name]
        self.framework.actuate_settings()

    def available_frameworks(self):
        """
        Print the names of all available frameworks.
        """
        for framework in self.frameworks.keys():
            print(framework)

    def set_getter(self, adjective_name: str, getter: Callable[[Any], Any]):
        """
        Overrides the getter function set during the adjective declaration.

        :param adjective_name: The name of the adjective to set the getter for.
        :type adjective_name: str
        :param getter: The getter function to set.
        :type getter: Callable[[Any], Any]
        :warning: No safety checks are performed when setting the getter directly.
        """
        self.framework.get_adjective(adjective_name)._set_getter(getter)

    def evaluate(self, node: Any, adjective_name: str, comparison_node: Any = None) -> Any:
        """
        Evaluate a node for a specific adjective.

        :param node: The node to evaluate.
        :type node: Any
        :param adjective_name: The name of the adjective to evaluate.
        :type adjective_name: str
        :param comparison_node: The other node involved in a comparison (if applicable).
        :type comparison_node: Any, optional
        :return: The result of the evaluation.
        :rtype: Any
        """
        adjective = self.framework.get_adjective(adjective_name)

        if comparison_node:
            return adjective.evaluate(node, comparison_node)
        else:
            return adjective.evaluate(node)

    def explain(self, node: Any, adjective_name: str, comparison_node: Any = None, *, 
                with_framework: str = None, explanation_depth: int = None, print_depth: int = None) -> Any:
        """
        Generate a propositional logic explanation for why a node has a specific adjective.

        :param node: The node to explain.
        :type node: Any
        :param adjective_name: The name of the adjective to explain.
        :type adjective_name: str
        :param comparison_node: The other node involved in a comparison (if applicable).
        :type comparison_node: Any, optional
        :param with_framework: Temporary framework to use for this explanation.
        :type with_framework: str, optional
        :param explanation_depth: Temporary explanation depth for this explanation.
        :type explanation_depth: int, optional
        :param print_depth: Temporary print depth for this explanation.
        :type print_depth: int, optional
        :return: An Implies implication representing the explanation of the adjective's affirmation.
        :rtype: Implies
        :raises ValueError: If the node is None.
        :raises KeyError: If no adjective with the given name is found.
        :raises CannotBeEvaluated: If the adjective cannot be evaluated on the given node.
        """
        if node is None:
            raise ValueError("The node you are asking about is non-existent. This might happen because of async processing. Try to run again.")

        # Handle temporary settings for this explanation
        prev_framework = self.settings.with_framework
        prev_explanation_depth = self.framework.settings.explanation_depth
        prev_print_depth = self.framework.settings.print_depth

        try:
            if with_framework is not None:
                self.settings.with_framework = with_framework
                self.select_framework(with_framework)

            if explanation_depth is not None:
                self.framework.settings.explanation_depth = explanation_depth

            if print_depth is not None:
                self.framework.settings.print_depth = print_depth

            adjective = self.framework.get_adjective(adjective_name)
            adjective.init_explanations_book()

            if not comparison_node:
                explanation = adjective.explain(node, current_explanation_depth=STARTING_EXPLANATION_DEPTH)
            else:
                explanation = adjective.explain(node, comparison_node, current_explanation_depth=STARTING_EXPLANATION_DEPTH)

            if isinstance(explanation, Implies):
                explanation._str_settings(print_first=True)

            context_str = f"Given:\n {node.parent_state}\n" if hasattr(node, "parent_state") else ""
            return f"{context_str}{explanation}"

            #return explanation

        except CannotBeEvaluated as e:
            to_return = f"The adjective \"{adjective_name}\" cannot be evaluated on the {self.framework.refer_to_nodes_as} {node}."
            if adjective_name != e.adjective_name:
                to_return += f" That is because {e.message}"
            return to_return
        except Exception as e:
            print(f"An unexpected error occurred while generating the explanation: {str(e)}")
            raise
        finally:
            # Reset settings for future explanations
            self.settings.with_framework = prev_framework
            self.select_framework(prev_framework)
            self.framework.settings.explanation_depth = prev_explanation_depth
            self.framework.settings.print_depth = prev_print_depth

    def add_explanation_tactic(self, tactic: 'Tactic', *, to_adjective: str = '', to_framework: str):
        """
        Add an explanation tactic to a specific framework or adjective.

        :param tactic: The tactic to add.
        :type tactic: Tactic
        :param to_adjective: The name of the adjective to add the tactic to. If empty, adds to the framework.
        :type to_adjective: str, optional
        :param to_framework: The name of the framework to add the tactic to.
        :type to_framework: str
        """
        framework = self.frameworks[to_framework]
        perform_on = framework.get_adjective(to_adjective) if to_adjective else framework

        tactics_to_add = [tactic]
        for requirement in tactic.requirements:
            tactics_to_add.append(requirement[0](*requirement[1]))

        perform_on._add_explanation_tactics(tactics_to_add)

    def del_explanation_tactic(self, tactic_class_name: str, *, to_adjective: str = '', to_framework: str):
        """
        Delete an explanation tactic from a specific framework or adjective.

        :param tactic_class_name: The name of the tactic class to delete.
        :type tactic_class_name: str
        :param to_adjective: The name of the adjective to delete the tactic from. If empty, deletes from the framework.
        :type to_adjective: str, optional
        :param to_framework: The name of the framework to delete the tactic from.
        :type to_framework: str
        """
        framework = self.frameworks[to_framework]
        perform_on = framework.get_adjective(to_adjective) if to_adjective else framework

        tactic = perform_on.get_explanation_tactic(tactic_class_name)

        tactics_to_delete_names = [tactic_class_name]
        for requirement in tactic.get_requirements():
            tactics_to_delete_names.append(requirement.name)

        perform_on._del_explanation_tactics(tactics_to_delete_names)

    def configure_settings(self, settings_dict: Dict[str, Any]):
        """
        Configure settings using a dictionary.

        :param settings_dict: A dictionary containing setting names and values.
        :type settings_dict: Dict[str, Any]
        """
        self.settings.configure(settings_dict)

        if 'with_framework' in settings_dict:
            self.select_framework(self.settings.with_framework)