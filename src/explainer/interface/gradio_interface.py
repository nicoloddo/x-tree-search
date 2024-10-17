from typing import Dict
import gradio as gr
import tempfile
import inspect
import sys
import graphviz
import re

from src.explainer.adjective import Adjective, AdjectiveType
from src.explainer.explanation import Explanation, Assumption, CompositeExplanation, ConditionalExplanation
from src.explainer.explanation_settings import ExplanationSettings
from src.explainer.framework import ArgumentationFramework
from src.explainer.propositional_logic import LogicalExpression, Implies

from src.explainer.explanation_settings import (
    EXPLANATION_DEPTH_ALLOWED_VALUES,
    ASSUMPTIONS_VERBOSITY_ALLOWED_VALUES,
    PRINT_MODE_ALLOWED_VALUES
)

# Dynamically get all adjective and explanation classes
adjective_classes = {name: cls for name, cls in inspect.getmembers(sys.modules['src.explainer.adjective'], inspect.isclass) 
                     if issubclass(cls, Adjective) and cls is not Adjective}
explanation_classes = {name: cls for name, cls in inspect.getmembers(sys.modules['src.explainer.explanation'], inspect.isclass) 
                       if issubclass(cls, Explanation) and cls is not Explanation}

class Node:
    """Represents a node in the explanation graph."""
    def __init__(self, id, type, adjective):
        self.id = id
        self.type = type
        self.adjective = adjective
        self.explanation = adjective.explanation

class ExplainerGradioInterface:
    """Main class for building and managing the explainer interface."""

    # Define tab IDs for the interface
    tab_ids = {
        "ai_explanation": 1,
        "visualize": 2,
        "visualize_decision_tree": 3,
        "settings": 4,
        "other": 5
    }

    # Define patterns for node hyperlinks
    node_hyperlink_prefix = "::node::"
    node_hyperlink_pattern = r'::node::\((.*?)\)\[(.*?)\]'

    # HTML template for cool text container
    cool_html_text_container = """<pre style="
        font-family: var(--font-mono); 
        font-size: var(--text-sm); 
        background: var(--code-background-fill); 
        overflow: auto;
        border-radius: var(--radius-sm);
        padding: var(--spacing-lg) var(--spacing-xl);">{}</pre>"""
    
    @classmethod
    def transform_hyperlink_to_node_id(cls, node_id):
        """
        Transform the hyperlink to the node id.

        :param node_id: The hyperlink or node ID string
        :return: The extracted node ID
        """
        match = re.search(cls.node_hyperlink_pattern, node_id)
        
        if match:
            node_id = match.group(1)
            node_title = match.group(2)
            return node_id
        else:
            return node_id

    def __init__(self, *, explainer=None, explain_in_hyperlink_mode=True):
        """
        Initialize the ExplainerInterface with an optional explainer.

        :param explainer: The explainer instance to use
        :param explain_in_hyperlink_mode: Whether to use hyperlink mode for explanations
        """
        self.nodes = {}

        self.init_explainer = explainer
        self.framework = explainer.framework or ArgumentationFramework(refer_to_nodes_as="node")
        self.load_framework()
        self.explain_in_hyperlink_mode = explain_in_hyperlink_mode

        self.graph_visualizer = self.GraphVisualizer(self.nodes, depth=3, get_adjective_names=self.get_adjective_names)
        self.ai_explainer = self.AIExplainer(self.init_explainer, explain_in_hyperlink_mode)
        self.interface_builder = self.InterfaceBuilder(
            explainer=self.init_explainer,
            tab_ids=ExplainerGradioInterface.tab_ids,
            explain_in_hyperlink_mode=explain_in_hyperlink_mode,
            get_adjective_names=self.get_adjective_names,
            update_ai_explanation=self.ai_explainer.update_ai_explanation,
            check_if_comparison_adjective=self.check_if_comparison_adjective,
            visualize_decision_tree=self.ai_explainer.visualize_decision_tree,
            visualize_graph=self.graph_visualizer.visualize_graph,
            apply_explainer_settings=self.apply_explainer_settings
        )

    def on_load(self, request: gr.Request):
        """
        On load event handler for the Gradio interface.

        :param request: The Gradio request object
        """
        if request:
            query_params = dict(request.query_params)
            # Note: Tab selector functionality is currently not working in Gradio
            """
            if 'tab' in query_params:
                tab = query_params['tab']
                return gr.Tabs(selected=self.tab_ids[tab])
            """

    def load_framework(self):
        """Load the adjectives from the framework."""
        for adjective in self.framework.adjectives.values():
            self._add_adjective(adjective)

    def _add_adjective(self, adjective):
        """
        Add an adjective to the graph.

        :param adjective: The adjective to add
        """
        node = Node(adjective.name, type(adjective).__name__, adjective)
        self.nodes[node.id] = node

    def get_adjective_names(self):
        """
        Get a list of all adjective names in the graph.

        :return: List of adjective names
        """
        return list(self.nodes.keys())

    def apply_explainer_settings(self, explainer, with_framework, explanation_depth, assumptions_verbosity, print_depth, print_implicit_assumptions, print_mode):
        """
        Apply the explainer settings.

        :param explainer: The explainer instance
        :param with_framework: Whether to use the framework
        :param explanation_depth: The depth of explanations
        :param assumptions_verbosity: The verbosity level for assumptions
        :param print_depth: Whether to print depth information
        :param print_implicit_assumptions: Whether to print implicit assumptions
        :param print_mode: The print mode for explanations
        :return: The updated explainer instance
        """
        settings_dict = {
            'with_framework': with_framework,
            'explanation_depth': explanation_depth,
            'assumptions_verbosity': assumptions_verbosity,
            'print_depth': print_depth,
            'print_implicit_assumptions': print_implicit_assumptions,
            'print_mode': print_mode
        }
        explainer.configure_settings(settings_dict)
        return explainer
    
    def check_if_comparison_adjective(self, adjective_name):
        """
        Check if the adjective name is a comparison adjective.

        :param adjective_name: The name of the adjective to check
        :return: Gradio update object with visibility and value
        """
        if adjective_name is None or adjective_name == "" or self.framework is None:
            return gr.update(visible=False, value=None)
        adjective = self.framework.get_adjective(adjective_name)
        if adjective.type == AdjectiveType.COMPARISON:
            return gr.update(visible=True, value=None)
        else:
            return gr.update(visible=False, value=None)
    
    def launch(self):
        """Launch the Gradio interface."""
        self.demo = self.interface_builder.build_interface()
        self.demo.launch()

    class InterfaceBuilder:
        """Class for building the Gradio interface components."""

        def __init__(self, **kwargs):
            self.init_explainer = kwargs.get('explainer')
            self.tab_ids = kwargs.get('tab_ids')
            self.explain_in_hyperlink_mode = kwargs.get('explain_in_hyperlink_mode')
            self.get_adjective_names = kwargs.get('get_adjective_names')
            self.update_ai_explanation = kwargs.get('update_ai_explanation')
            self.check_if_comparison_adjective = kwargs.get('check_if_comparison_adjective')
            self.visualize_decision_tree = kwargs.get('visualize_decision_tree')
            self.visualize_graph = kwargs.get('visualize_graph')
            self.apply_explainer_settings = kwargs.get('apply_explainer_settings')
        
        def update_dropdowns(self):
            """
            Update all dropdowns with current adjective names.

            :return: List of Gradio update objects for dropdowns
            """
            choices = self.get_adjective_names()
            return [gr.update(choices=choices, value=None) for _ in range(len(self.dropdown_components))]

        def get_decision_tree_legend(self, game):
            """
            Get the decision tree visualization legend.

            :param game: The game instance
            :return: The legend for the decision tree or None
            """
            return game.explaining_agent.core.visualize_legend_move_tree() if game.explaining_agent is not None else None

        def get_default_explainer_settings(self):
            """
            Returns the default explainer settings.

            :return: Dictionary of default settings
            """
            default_settings = ExplanationSettings.default_settings
            explainer = self.init_explainer
            default_settings = {
                "with_framework" : explainer.settings.with_framework,
                "assumptions_verbosity" : explainer.settings.assumptions_verbosity,
                "print_depth" : explainer.settings.print_depth,
                "print_implicit_assumptions" : explainer.settings.print_implicit_assumptions,
                "print_mode" : explainer.settings.print_mode
            } 
            return default_settings

        def reset_explainer_settings(self):
            """
            Reset the explainer settings to default values.

            :return: List of Gradio update objects for settings components
            """
            default_settings = self.get_default_explainer_settings()
            return [gr.update(value=default_settings[key]) for key in default_settings]
        
        def build_ai_explanation_components(self, game_state_component, explainer_state_component, toggles: Dict[str, tuple[str, bool]] = None, *, additional_info: str = None):
            """
            Build the AI explanation components.

            :param game_state_component: The game state component
            :param explainer_state_component: The explainer state component
            :param toggles: A dictionary of toggles to add to the interface
            :param additional_info: Additional information to display
            :return: Dictionary of created components
            """
            components = {}
            
            # Build input components
            with gr.Row():
                with gr.Column(scale=1):
                    components["id_input"] = gr.Textbox(label="Ask further about (you can drag and drop a move from the explanation)", visible=self.explain_in_hyperlink_mode)
                with gr.Column(scale=1):
                    components["explain_adj_name"] = gr.Dropdown(choices=self.get_adjective_names(), label="Why is it ...? Why it has that ...?", visible=self.explain_in_hyperlink_mode)
            components["comparison_id_input"] = gr.Textbox(label="In comparison to (you can drag and drop from the explanation)", visible=False)
            
            # Hidden components for storing current state
            components["current_node_id"] = gr.Textbox(label="Current Node ID", visible=False)
            components["current_adjective"] = gr.Textbox(label="Current Adjective", visible=False)
            components["current_comparison_id"] = gr.Textbox(label="Current Comparison ID", visible=False)

            # Explanation button and depth slider
            components["explain_button"] = gr.Button("Explain", visible=self.explain_in_hyperlink_mode)
            default_explanation_depth = self.init_explainer.settings.explanation_depth if self.init_explainer is not None else ExplanationSettings.default_settings["explanation_depth"]
            components["explanation_depth"] = gr.Slider(minimum=min(EXPLANATION_DEPTH_ALLOWED_VALUES), maximum=max(EXPLANATION_DEPTH_ALLOWED_VALUES), step=1, value=default_explanation_depth, label="Explanation Depth")

            # Explanation output components
            components["explaining_question"] = gr.HTML(value=ExplainerGradioInterface.cool_html_text_container.format("Why ...?"), label="Question", visible=self.explain_in_hyperlink_mode)
            if self.explain_in_hyperlink_mode and additional_info is not None:
                components["additional_info"] = gr.HTML(value=ExplainerGradioInterface.cool_html_text_container.format(additional_info))
            
            if self.explain_in_hyperlink_mode:
                components["explanation_output"] = gr.HTML(value=self.update_ai_explanation(game_state_component.value, explainer_state_component.value)[0], label="AI move explanation")
            else:
                components["explanation_output"] = gr.Markdown(value="", label="AI move explanation")

            # Add toggles if provided
            if toggles:
                for name, toggle_params in toggles.items():
                    label, value = toggle_params
                    components[name] = gr.Checkbox(label=label, value=value)

            return components

        def build_visualize_components(self):
            """
            Build the visualize components for the framework graph.

            :return: Dictionary of created components
            """
            components = {}
            gr.Markdown("""# Visualize the chain of explanations defined in the framework
                        You can zoom in through the browser, just wait for the graph to load.
                        Consider opening the image in a new tab for a better experience.""")
            components["root_adjective"] = gr.Dropdown(choices=self.get_adjective_names(), label="Select Root Adjective (optional)")
            components["visualize_button"] = gr.Button("Visualize Framework")
            components["graph_output"] = gr.Image(label="")

            return components
        
        def build_visualize_decision_tree_components(self, game_state_component):
            """
            Build components for visualizing the Decision Tree.

            :param game_state_component: The game state component
            :return: Dictionary of created components
            """
            components = {}
            
            gr.Markdown("""# Visualize the Decision Tree
                        ### Here you can visualize the AI's decision making tree and understand better the level of complexity that the explainer is elaborating on.
                        
                        You can zoom in through the browser, just wait for the graph to load.
                        Consider opening the image in a new tab for a better experience.""")
            legend = self.get_decision_tree_legend(game_state_component.value)
            components["move_tree_legend"] = gr.Image(value=legend, interactive=False)
            components["visualize_decision_tree_button"] = gr.Button("Generate Decision Tree")
            components["move_tree_output"] = gr.Image(label="", interactive=False)

            return components

        def build_explainer_settings_components(self):
            """
            Build components for explainer settings.

            :return: Dictionary of created components
            """
            components = {}

            default_values = self.get_default_explainer_settings()            

            with gr.Row():
                with gr.Column(scale=1):
                    components["with_framework"] = gr.Textbox(
                        label="Framework Name", 
                        value=default_values["with_framework"],
                        visible=False)  # Currently not customizable
                    
                    # Explanation Depth setting has been moved to the AI explanation section

                    components["assumptions_verbosity"] = gr.Dropdown(
                        choices=ASSUMPTIONS_VERBOSITY_ALLOWED_VALUES,
                        label="Assumptions Verbosity",
                        value=default_values["assumptions_verbosity"]
                    )
                
                with gr.Column(scale=1):
                    components["print_depth"] = gr.Checkbox(label="Print Depth", value=default_values["print_depth"])
                    components["print_implicit_assumptions"] = gr.Checkbox(label="Print Implicit Assumptions", value=default_values["print_implicit_assumptions"])
                    components["print_mode"] = gr.Dropdown(
                        choices=PRINT_MODE_ALLOWED_VALUES,
                        label="Print Mode",
                        value=default_values["print_mode"]
                    )
            
            components["apply_settings_button"] = gr.Button("Apply Settings")

            return components

        def connect_components(self, components, game_state_component, explainer_state_component):
            """
            Connect the components of the interface.

            :param components: The components to connect
            :param game_state_component: The game state component
            :param explainer_state_component: The explainer state component
            """
            # Explain button functionality
            if "explain_button" in components:
                components["explain_button"].click(
                    self.update_ai_explanation,
                    inputs=[game_state_component, explainer_state_component, components["id_input"], components["explain_adj_name"], components["comparison_id_input"], components["explanation_depth"]],
                    outputs=[components["explanation_output"], components["explaining_question"], components["current_node_id"], components["current_adjective"], components["current_comparison_id"]]
                )
                components["explanation_depth"].change(
                    self.update_ai_explanation,
                    inputs=[game_state_component, explainer_state_component, components["id_input"], components["explain_adj_name"], components["comparison_id_input"], components["explanation_depth"]],
                    outputs=[components["explanation_output"], components["explaining_question"], components["current_node_id"], components["current_adjective"], components["current_comparison_id"]]
                )
                components["id_input"].change(
                    ExplainerGradioInterface.transform_hyperlink_to_node_id,
                    inputs=[components["id_input"]],
                    outputs=[components["id_input"]]
                )
                components["explain_adj_name"].change(
                    self.check_if_comparison_adjective,
                    inputs=[components["explain_adj_name"]],
                    outputs=[components["comparison_id_input"]]
                )
                components["comparison_id_input"].change(
                    ExplainerGradioInterface.transform_hyperlink_to_node_id,
                    inputs=[components["comparison_id_input"]],
                    outputs=[components["comparison_id_input"]]
                )
                components["explanation_output"].change( # Make the explanation output draggable
                    fn=None,  # No Python function needed
                    inputs=None,
                    outputs=None,
                    js="""
                    (explanation) => {
                        document.querySelectorAll('.draggable-node').forEach(node => {
                            node.draggable = true;
                            node.addEventListener('dragstart', (e) => {
                                e.dataTransfer.setData('text/plain', node.dataset.node);
                            });
                        });
                        return explanation;  // Return the input to satisfy Gradio's expectation
                    }
                    """
                )

            # Visualize framework graph
            if "visualize_button" in components:
                components["visualize_button"].click(
                    self.visualize_graph, 
                    inputs=[components["root_adjective"]], 
                    outputs=[components["graph_output"]]
                )

            # Visualize Decision Tree
            if "visualize_decision_tree_button" in components:
                components["visualize_decision_tree_button"].click(
                    self.visualize_decision_tree,
                    inputs=[game_state_component],
                    outputs=[components["move_tree_output"]]
                )

            # Apply explainer settings
            if "apply_settings_button" in components:
                components["apply_settings_button"].click(
                    self.apply_explainer_settings,
                    inputs=[explainer_state_component, components["with_framework"], components["explanation_depth"], components["assumptions_verbosity"], 
                            components["print_depth"], components["print_implicit_assumptions"], components["print_mode"]],
                    outputs=[explainer_state_component]
                )

            # Update dropdowns
            self.dropdown_components = [comp for comp in [components.get("root_adjective"), 
                                                    components.get("explain_adj_name")] if comp is not None]
            if self.dropdown_components:
                for button in []:  # No buttons need to update the dropdowns right now
                    if button:
                        button.click(self.update_dropdowns, outputs=self.dropdown_components)

        def build_interface(self):
            """
            Build the complete Gradio interface.

            :return: The Gradio Blocks object representing the interface
            """
            with gr.Blocks() as demo:
                gr.Markdown("# X-Tree-Search Explainer")
                
                with gr.Tabs():
                    with gr.TabItem("Explain", id=self.tab_ids["ai_explanation"]):
                        ai_explanation_components = self.build_ai_explanation_components()
                    with gr.TabItem("Visualize Framework", id=self.tab_ids["visualize"]):
                        visualize_components = self.build_visualize_components()
                    with gr.TabItem("Visualize Decision Tree", id=self.tab_ids["move_tree"]):
                        move_tree_components = self.build_visualize_decision_tree_components()
                    with gr.TabItem("Settings", id=self.tab_ids["settings"]):
                        settings_components = self.build_explainer_settings_components()

                components = {**ai_explanation_components, **visualize_components, **move_tree_components, **settings_components}

                # Connect components
                self.connect_components(components)

            return demo
        
    class AIExplainer:
        """Class for handling AI explanations."""

        def __init__(self, explainer, explain_in_hyperlink_mode):
            self.init_explainer = explainer
            self.explain_in_hyperlink_mode = explain_in_hyperlink_mode
        
        def update_ai_explanation(self, game, explainer, node_id=None, adjective=None, comparison_id=None, explanation_depth=None):
            """
            Update the AI explanation.

            :param game: The game instance
            :param explainer: The explainer instance
            :param node_id: The ID of the node to explain
            :param adjective: The adjective to use in the explanation
            :param comparison_id: The ID of the node to compare with
            :param explanation_depth: The depth of the explanation
            :return: Tuple containing the explanation, question, and current state information
            """
            current_node_id = ''
            current_comparison_id = ''
            current_adjective = ''

            # Handle empty inputs
            if node_id == '':
                node_id = None
            if adjective == '':
                adjective = None
            if comparison_id == '':
                comparison_id = None

            explanation = ""
            explaining_question = "Why ...?"
            
            # Check for valid inputs
            if adjective is None:
                explanation = "No adjective was provided."
            elif not game:
                explanation = "No game was provided."
            elif game.explaining_agent is None:
                explanation = "No explaining agent was found."
            else:
                # Set explanation depth
                if explanation_depth is None:
                    explanation_depth = explainer.settings.explanation_depth
                else:
                    explanation_depth = int(explanation_depth)
            
                # Get the node to explain
                if node_id is None:
                    node = game.explaining_agent.choice
                    if node is not None:
                        node_id = node.id
                else:
                    node = game.explaining_agent.core.nodes[node_id]
                
                if node is None:
                    explanation = f"No {explainer.framework.refer_to_nodes_as} to explain was found."
                else:
                    # Generate explanation
                    if self.explain_in_hyperlink_mode:
                        activated = LogicalExpression.set_hyperlink_mode(self.explain_in_hyperlink_mode, node.__class__)
                    else:
                        activated = False

                    current_node_id = node.id
                    current_adjective = adjective
                    if comparison_id is None:
                        explanation = explainer.explain(node, adjective, print_context=False, explanation_depth=explanation_depth)
                    else:
                        current_comparison_id = comparison_id
                        comparison_node = game.explaining_agent.core.nodes[comparison_id]
                        explanation = explainer.explain(node, adjective, comparison_node, print_context=False, explanation_depth=explanation_depth)

                    # Build explaining question
                    if isinstance(explanation, Implies):
                        explanation.consequent.build_str_components()
                        verb_str = explanation.consequent.verb_str
                        predicate_str = explanation.consequent.predicate_str
                        
                        object_str = explanation.consequent.object_str
                        if object_str.count(ExplainerGradioInterface.node_hyperlink_prefix) == 1: # We are simply comparing two nodes
                            object_str = f" {comparison_node.game_tree_node_string} [id: {comparison_node.id}]"                            

                        explaining_question = f"Why {verb_str} {node.game_tree_node_string} [id: {node.id}]{' that' if verb_str != 'is' else ''} {predicate_str}{object_str}?"
                    else:
                        explaining_question = f""
                        
                    explanation = str(explanation)

                    # If we are in interface mode, we need to replace the node references with hyperlinks
                    if activated:
                        LogicalExpression.set_hyperlink_mode(False)
                        explanation = re.sub(
                            ExplainerGradioInterface.node_hyperlink_pattern,
                            lambda m: f'<span class="draggable-node" data-node="{ExplainerGradioInterface.node_hyperlink_prefix}({m.group(1)})[{m.group(2)}]" title="{m.group(1)}" style="cursor: grab; color: var(--color-accent); font-weight: bold;">{m.group(2)}</span>',
                            explanation
                        )

            # Format the explanation output
            if self.explain_in_hyperlink_mode:
                full_return = ExplainerGradioInterface.cool_html_text_container.format(explanation)
            else:
                full_return = f"```markdown\n{explanation}\n```"

            explaining_question = ExplainerGradioInterface.cool_html_text_container.format(explaining_question)

            return full_return, explaining_question, current_node_id, current_adjective, current_comparison_id

        def visualize_decision_tree(self, game):
            """
            Generate a visualization of the Decision Tree.

            :param game: The game instance
            :return: The visualization of the decision tree
            :raises gr.Error: If there's an error in generating the visualization
            """
            root_node = game.explaining_agent.choice.parent
            try:
                return game.explaining_agent.core.visualize_decision_tree(root_node)
            except Exception as e:
                raise gr.Error(f"Error: {e}")

    class GraphVisualizer:
        """Class for visualizing the explanation graph."""
        def __init__(self, nodes, depth, get_adjective_names):
            self.nodes = nodes
            self.explanation_depth = depth
            self.get_adjective_names = get_adjective_names

        def visualize_graph(self, root_adjective=None, debug=False):
            """
            Generate a visualization of the subgraph starting from the given root adjective.
            
            :param root_adjective: The starting point for visualization. If None, visualize all adjectives.
            :param debug: If True, display the graph using matplotlib for debugging.
            :return: Path to the generated PNG file.
            """
            # Initialize the graph
            dot = self._initialize_graph()
            
            # Set of processed nodes to avoid duplicates
            processed_nodes = set()
            
            # Adjust explanation depth for full visualization if no root is specified
            original_depth = self.explanation_depth
            if root_adjective is None:
                self.explanation_depth = float('inf')
            
            # Process nodes
            if root_adjective:
                if root_adjective not in self.nodes:
                    return None
                self._process_node(dot, root_adjective, processed_nodes, is_root=True)
            else:
                for node_id in self.nodes:
                    self._process_node(dot, node_id, processed_nodes, is_root=True)
            
            # Restore original explanation depth
            self.explanation_depth = original_depth
            
            # Render and save the graph
            rendered_filename = self._render_graph(dot)
            
            # Debug visualization if requested
            if debug:
                self._debug_display(rendered_filename)
            
            return rendered_filename

        def _initialize_graph(self):
            """Initialize and configure the graphviz Digraph object."""
            dot = graphviz.Digraph(comment='Explanation Flowchart')
            dot.attr(rankdir='LR')  # Left to Right layout
            dot.attr('node', shape='rectangle', style='rounded,filled', fontname='Arial', fontsize='10')
            dot.attr('edge', fontname='Arial', fontsize='8')
            return dot

        def _process_node(self, dot, node_id, processed_nodes, parent_id=None, explanation_depth=0, is_root=False):
            """
            Recursively process a node and its explanations, adding them to the graph.
            
            :param dot: The graphviz Digraph object.
            :param node_id: ID of the node to process.
            :param processed_nodes: Set of already processed node IDs.
            :param parent_id: ID of the parent node, if any.
            :param explanation_depth: Current depth of explanation.
            :param is_root: Whether this node is a root node.
            """
            explanation_depth += 1
            node = self.nodes[node_id]
            
            # Handle duplicate nodes
            is_duplicate, node_id = self._handle_duplicate_node(node_id, processed_nodes)
            
            # Add node to graph
            self._add_node_to_graph(dot, node_id, node, is_root)
            if parent_id:
                dot.edge(parent_id, node_id)
            processed_nodes.add(node_id)
            
            # Process explanation if within depth limit and not a duplicate (or is root)
            if explanation_depth < self.explanation_depth and (not is_duplicate or is_root) and node.explanation:
                self._process_explanation(dot, node_id, node.explanation, f"{node_id}_exp", processed_nodes, explanation_depth)

        def _handle_duplicate_node(self, node_id, processed_nodes):
            """Handle duplicate nodes by creating a new ID if necessary."""
            if node_id in processed_nodes:
                suffix = 1
                while f"{node_id}_copy{suffix}" in processed_nodes:
                    suffix += 1
                return True, f"{node_id}_copy{suffix}"
            return False, node_id

        def _add_node_to_graph(self, dot, node_id, node, is_root):
            """Add a node to the graph with appropriate styling."""
            label = f"{node.id}\n{node.type}"
            color = 'pink' if is_root else 'lightblue'
            dot.node(node_id, label, fillcolor=color)

        def _process_explanation(self, dot, parent_id, explanation, exp_id, processed_nodes, explanation_depth, edge_label=None):
            """
            Process an explanation, adding it and its components to the graph.
            
            :param dot: The graphviz Digraph object.
            :param parent_id: ID of the parent node.
            :param explanation: The explanation object to process.
            :param exp_id: ID for this explanation node.
            :param processed_nodes: Set of already processed node IDs.
            :param explanation_depth: Current depth of explanation.
            :param edge_label: Label for the edge connecting to parent, if any.
            """
            exp_label = type(explanation).__name__

            if isinstance(explanation, Assumption):
                dot.node(exp_id, f"{exp_label}\n{explanation.description}", fillcolor='lightgreen')
                dot.edge(parent_id, exp_id, label=edge_label)
            elif isinstance(explanation, CompositeExplanation):
                dot.node(exp_id, exp_label, fillcolor='green')
                dot.edge(parent_id, exp_id, label=edge_label)
                for i, sub_exp in enumerate(explanation.explanations):
                    self._process_explanation(dot, exp_id, sub_exp, f"{exp_id}_sub_{i}", processed_nodes, explanation_depth)
            elif isinstance(explanation, ConditionalExplanation):
                self._process_conditional_explanation(dot, parent_id, explanation, exp_id, processed_nodes, explanation_depth, edge_label)
            else:
                self._process_generic_explanation(dot, parent_id, explanation, exp_id, processed_nodes, explanation_depth, edge_label)

        def _process_conditional_explanation(self, dot, parent_id, explanation, exp_id, processed_nodes, explanation_depth, edge_label):
            """Process a conditional explanation, adding condition and branches to the graph."""
            condition_id = f"{exp_id}_condition"
            dot.node(condition_id, f"If\n{explanation.condition.description}", fillcolor='yellow')
            dot.edge(parent_id, condition_id, label=edge_label)

            self._process_explanation(dot, condition_id, explanation.explanation_if_true, f"{exp_id}_true", processed_nodes, explanation_depth, 'True')
            self._process_explanation(dot, condition_id, explanation.explanation_if_false, f"{exp_id}_false", processed_nodes, explanation_depth, 'False')

        def _process_generic_explanation(self, dot, parent_id, explanation, exp_id, processed_nodes, explanation_depth, edge_label):
            """Process a generic explanation, adding its components to the graph."""
            dot.node(exp_id, type(explanation).__name__, fillcolor='lightgreen')
            dot.edge(parent_id, exp_id, label=edge_label)
            for key, value in explanation.__dict__.items():
                if key != "explanation_of_adjective" and isinstance(value, str) and value in self.get_adjective_names():
                    self._process_node(dot, value, processed_nodes, parent_id=exp_id, explanation_depth=explanation_depth)

        def _render_graph(self, dot):
            """Render the graph to a temporary PNG file and return the filename."""
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_filename = tmp_file.name

            dot.attr(dpi='300')  # Set high resolution
            dot.render(tmp_filename, format='png', cleanup=True)
            
            return tmp_filename + '.png'

        def _debug_display(self, filename):
            """Display the graph using matplotlib for debugging purposes."""
            import matplotlib.pyplot as plt
            import matplotlib.image as mpimg

            img = mpimg.imread(filename)
            plt.figure(figsize=(20, 20))
            plt.imshow(img)
            plt.axis('off')
            plt.show()

if __name__ == "__main__":
    if True:
        from explainers.alphabeta_explainer import AlphaBetaExplainer
        explainer = AlphaBetaExplainer()
        builder = ExplainerGradioInterface(explainer=explainer, explanation_depth=3)
        builder.launch()
        #builder.visualize_graph("as next move", debug=True)
        #builder.visualize_graph("as next move")