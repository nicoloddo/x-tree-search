from typing import Dict
import gradio as gr
import tempfile
import inspect
import sys
import graphviz
import re
from urllib.parse import urlencode

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
    tab_ids = {
        "ai_explanation": 1,
        "visualize": 2,
        "visualize_decision_tree": 3,
        "settings": 4,
        "other": 5
    }

    cool_html_text_container = """<pre style="
        font-family: var(--font-mono); 
        font-size: var(--text-sm); 
        background: var(--code-background-fill); 
        overflow: auto;
        border-radius: var(--radius-sm);
        padding: var(--spacing-lg) var(--spacing-xl);">{}</pre>"""

    """Main class for building and managing the explainer interface."""
    def __init__(self, *, framework=None, explain_in_hyperlink_mode=True):
        """Initialize the ExplainerInterface with an optional game to explain."""
    
        self.game = None
        self.explaining_agent = None
        self.framework = framework
        self.explain_in_hyperlink_mode = explain_in_hyperlink_mode

        self.nodes = {}

        self.graph_visualizer = self.GraphVisualizer(self.nodes, depth=3, get_adjective_names=self.get_adjective_names)
        self.ai_explainer = self.AIExplainer(self.get_game, self.get_explaining_agent, explain_in_hyperlink_mode)
        self.interface_builder = self.InterfaceBuilder(
            get_game=self.get_game,
            get_explaining_agent=self.get_explaining_agent,
            tab_ids=ExplainerGradioInterface.tab_ids,
            explain_in_hyperlink_mode=explain_in_hyperlink_mode,
            get_adjective_names=self.get_adjective_names,
            update_ai_explanation=self.ai_explainer.update_ai_explanation,
            transform_hyperlink_to_node_id=self.transform_hyperlink_to_node_id,
            check_if_comparison_adjective=self.check_if_comparison_adjective,
            visualize_decision_tree=self.ai_explainer.visualize_decision_tree,
            visualize_graph=self.graph_visualizer.visualize_graph,
            apply_explainer_settings=self.apply_explainer_settings
        )
    
    def set_game(self, game):
        self.game = game

        if self.game:
            self.framework = self.game.explainer.framework or ArgumentationFramework(refer_to_nodes_as="node")
        
        self.load_framework()

    def get_game(self):
        return self.game

    def set_explaining_agent(self, explaining_agent):
        self.explaining_agent = explaining_agent

    def get_explaining_agent(self):
        return self.explaining_agent

    def on_load(self, request: gr.Request):
        """
        On load event handler.
        """
        if request:
            query_params = dict(request.query_params)
            """The tab selector does not work right now on Gradio
            if 'tab' in query_params:
                tab = query_params['tab']
                return gr.Tabs(selected=self.tab_ids[tab])"""

    def load_framework(self):
        """Load the adjectives from the framework."""
        for adjective in self.framework.adjectives.values():
            self._add_adjective(adjective)

    def _add_adjective(self, adjective):
        """Add an adjective to the graph."""
        node = Node(adjective.name, type(adjective).__name__, adjective)
        self.nodes[node.id] = node

    def get_adjective_names(self):
        """Get a list of all adjective names in the graph."""
        return list(self.nodes.keys())

    def apply_explainer_settings(self, with_framework, explanation_depth, assumptions_verbosity, print_depth, print_implicit_assumptions, print_mode):
        """Apply the explainer settings."""
        settings_dict = {
            'with_framework': with_framework,
            'explanation_depth': explanation_depth,
            'assumptions_verbosity': assumptions_verbosity,
            'print_depth': print_depth,
            'print_implicit_assumptions': print_implicit_assumptions,
            'print_mode': print_mode
        }
        if self.game is not None:
            self.game.explainer.configure_settings(settings_dict)
    
    def transform_hyperlink_to_node_id(self, node_id):
        """Transform the hyperlink to the node id."""
        if "http" in node_id:
            return node_id.split("show_node_id=")[1]
        else:
            return node_id
    
    def check_if_comparison_adjective(self, adjective_name):
        """Check if the adjective name is a comparison adjective."""
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
        def __init__(self, **kwargs):
            self.get_game = kwargs.get('get_game')
            self.get_explaining_agent = kwargs.get('get_explaining_agent')
            self.tab_ids = kwargs.get('tab_ids')
            self.explain_in_hyperlink_mode = kwargs.get('explain_in_hyperlink_mode')
            self.get_adjective_names = kwargs.get('get_adjective_names')
            self.update_ai_explanation = kwargs.get('update_ai_explanation')
            self.transform_hyperlink_to_node_id = kwargs.get('transform_hyperlink_to_node_id')
            self.check_if_comparison_adjective = kwargs.get('check_if_comparison_adjective')
            self.visualize_decision_tree = kwargs.get('visualize_decision_tree')
            self.visualize_graph = kwargs.get('visualize_graph')
            self.apply_explainer_settings = kwargs.get('apply_explainer_settings')

        @property
        def game(self):
            return self.get_game()
        @property
        def explaining_agent(self):
            return self.get_explaining_agent()
        
        def update_dropdowns(self):
            """Update all dropdowns with current adjective names."""
            choices = self.get_adjective_names()
            return [gr.update(choices=choices, value=None) for _ in range(4)]

        def update_explainer_settings(self):
            """Update the explainer settings."""
            default_settings = ExplanationSettings.default_settings
            if self.game is not None:
                explainer = self.game.explainer
                default_settings = {
                    "with_framework" : explainer.settings.with_framework,
                    "assumptions_verbosity" : explainer.settings.assumptions_verbosity,
                    "print_depth" : explainer.settings.print_depth,
                    "print_implicit_assumptions" : explainer.settings.print_implicit_assumptions,
                    "print_mode" : explainer.settings.print_mode
                } 
            
            return [gr.update(value=default_settings[key]) for key in default_settings]
        
        def build_ai_explanation_components(self, toggles: Dict[str, tuple[str, bool]] = None, *, additional_info: str = None):
            """
            Build the AI explanation components.

            :param toggles: A dictionary of toggles to add to the interface. 
            The key is the name of the toggle, the value is a tuple of the label and the value.
            """
            components = {}
            
            with gr.Row():
                with gr.Column(scale=1):
                    components["id_input"] = gr.Textbox(label="Ask further about (you can drag and drop a move from the explanation)", visible=self.explain_in_hyperlink_mode)
                with gr.Column(scale=1):
                    components["explain_adj_name"] = gr.Dropdown(choices=self.get_adjective_names(), label="Why is it ...? Why it has that ...?", visible=self.explain_in_hyperlink_mode)
            components["comparison_id_input"] = gr.Textbox(label="In comparison to (you can drag and drop from the explanation)", visible=False)
            components["explain_button"] = gr.Button("Explain", visible=self.explain_in_hyperlink_mode)

            default_explanation_depth = self.game.explainer.settings.explanation_depth if self.game is not None else ExplanationSettings.default_settings["explanation_depth"]
            components["explanation_depth"] = gr.Slider(minimum=min(EXPLANATION_DEPTH_ALLOWED_VALUES), maximum=max(EXPLANATION_DEPTH_ALLOWED_VALUES), step=1, value=default_explanation_depth, label="Explanation Depth")
            components["explaining_question"] = gr.HTML(value=ExplainerGradioInterface.cool_html_text_container.format("Why ...?"), label="Question", visible=self.explain_in_hyperlink_mode)
            if self.explain_in_hyperlink_mode and additional_info is not None:
                components["additional_info"] = gr.HTML(value=ExplainerGradioInterface.cool_html_text_container.format(additional_info))
            
            if self.explain_in_hyperlink_mode:
                components["explanation_output"] = gr.HTML(value=self.update_ai_explanation()[0], label="AI move explanation")
            else:
                components["explanation_output"] = gr.Markdown(value="", label="AI move explanation")

            if toggles:
                for name, toggle_params in toggles.items():
                    label, value = toggle_params
                    components[name] = gr.Checkbox(label=label, value=value)

            return components

        def build_visualize_components(self):
            """
            Build the visualize components.
            """
            components = {}
            gr.Markdown("""# Visualize the chain of explanations defined in the framework
                        You can zoom in through the browser, just wait for the graph to load.
                        Consider opening the image in a new tab for a better experience.""")
            components["root_adjective"] = gr.Dropdown(choices=self.get_adjective_names(), label="Select Root Adjective (optional)")
            components["visualize_button"] = gr.Button("Visualize Framework")
            components["graph_output"] = gr.Image(label="")

            return components
        
        def build_visualize_decision_tree_components(self):
            """Build components for visualizing the Decision Tree."""
            components = {}
            
            gr.Markdown("""# Visualize the Decision Tree
                        ### Here you can visualize the AI's decision making tree and understand better the level of complexity that the explainer is elaborating on.
                        
                        You can zoom in through the browser, just wait for the graph to load.
                        Consider opening the image in a new tab for a better experience.""")
            legend = self.explaining_agent.core.visualize_legend_move_tree() if self.explaining_agent is not None else None
            components["move_tree_legend"] = gr.Image(value=legend)
            components["visualize_decision_tree_button"] = gr.Button("Generate Decision Tree")
            components["move_tree_output"] = gr.Image(label="")

            return components

        def build_explainer_settings_components(self):
            """Build components for explainer settings."""
            components = {}

            default_values = ExplanationSettings.default_settings
            if self.game is not None:
                explainer = self.game.explainer
                default_values = {
                    "with_framework" : explainer.settings.with_framework,
                    "assumptions_verbosity" : explainer.settings.assumptions_verbosity,
                    "print_depth" : explainer.settings.print_depth,
                    "print_implicit_assumptions" : explainer.settings.print_implicit_assumptions,
                    "print_mode" : explainer.settings.print_mode
                }                

            with gr.Row():
                with gr.Column(scale=1):
                    components["with_framework"] = gr.Textbox(
                        label="Framework Name", 
                        value=default_values["with_framework"],
                        visible=False) # For now this is not customizable
                    
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

        def connect_components(self, components):
            """
            Connect the components of the interface.

            :param components: The components to connect.
            """
            # Explain
            if "explain_button" in components:
                components["explain_button"].click(
                    self.update_ai_explanation,
                    inputs=[components["id_input"], components["explain_adj_name"], components["comparison_id_input"], components["explanation_depth"]],
                    outputs=[components["explanation_output"], components["explaining_question"]]
                )
                components["explanation_depth"].change(
                    self.update_ai_explanation,
                    inputs=[components["id_input"], components["explain_adj_name"], components["comparison_id_input"], components["explanation_depth"]],
                    outputs=[components["explanation_output"], components["explaining_question"]]
                )
                components["id_input"].change(
                    self.transform_hyperlink_to_node_id,
                    inputs=[components["id_input"]],
                    outputs=[components["id_input"]]
                )
                components["explain_adj_name"].change(
                    self.check_if_comparison_adjective,
                    inputs=[components["explain_adj_name"]],
                    outputs=[components["comparison_id_input"]]
                )
                components["comparison_id_input"].change(
                    self.transform_hyperlink_to_node_id,
                    inputs=[components["comparison_id_input"]],
                    outputs=[components["comparison_id_input"]]
                )

            # Visualize
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
                    outputs=[components["move_tree_output"]]
                )

            # Settings
            if "apply_settings_button" in components:
                components["apply_settings_button"].click(
                    self.apply_explainer_settings,
                    inputs=[components["with_framework"], components["explanation_depth"], components["assumptions_verbosity"], 
                            components["print_depth"], components["print_implicit_assumptions"], components["print_mode"]],
                    outputs=[]
                )

            # Update dropdowns
            dropdown_components = [comp for comp in [components.get("root_adjective"), 
                                                    components.get("explain_adj_name")] if comp is not None]
            if dropdown_components:
                for button in []: #  No buttons need to update the dropdowns right now
                    if button:
                        button.click(self.update_dropdowns, outputs=dropdown_components)

        def build_interface(self):
            with gr.Blocks() as demo:
                gr.Markdown("# X-Tree-Search Explainer")
                
                with gr.Tabs():
                    with gr.TabItem("Explain", id=self.tab_ids["ai_explanation"]):
                        ai_explanation_components = self.build_ai_explanation_components()
                    with gr.TabItem("Visualize", id=self.tab_ids["visualize"]):
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
        def __init__(self, get_game, get_explaining_agent, explain_in_hyperlink_mode):
            self.get_game = get_game
            self.get_explaining_agent = get_explaining_agent
            self.explain_in_hyperlink_mode = explain_in_hyperlink_mode

        @property
        def game(self):
            return self.get_game()
        @property
        def explaining_agent(self):
            return self.get_explaining_agent()
        
        def update_ai_explanation(self, node_id=None, adjective=None, comparison_id=None, explanation_depth=None):
            """
            Update the AI explanation.

            :param node_id: The ID of the node to explain.
            :param adjective: The adjective to use in the explanation.
            """
            if node_id == '':
                node_id = None
            if comparison_id == '':
                comparison_id = None

            explanation = ""
            explaining_question = "Why ...?"
            
            if adjective is None:
                explanation = "No adjective was provided."
            elif not self.game:
                explanation = "No game was provided."
            elif self.explaining_agent is None:
                explanation = "No explaining agent was found."
            else:
                if explanation_depth is None:
                    explanation_depth = self.game.explainer.settings.explanation_depth
                else:
                    explanation_depth = int(explanation_depth)
            
                if node_id is None:
                    node = self.explaining_agent.choice
                    if node is not None:
                        node_id = node.id
                else:
                    node = self.explaining_agent.core.nodes[node_id]
                
                if node is None:
                    explanation = f"No {self.game.explainer.framework.refer_to_nodes_as} to explain was found."
                else:
                    # All is good, we can explain
                    if self.explain_in_hyperlink_mode:
                        activated = LogicalExpression.set_hyperlink_mode(self.explain_in_hyperlink_mode, node.__class__)
                    else:
                        activated = False

                    # Explain
                    if comparison_id is None:
                        explanation = self.game.explainer.explain(node, adjective, print_context=False, explanation_depth=explanation_depth)
                    else:
                        comparison_node = self.explaining_agent.core.nodes[comparison_id]
                        explanation = self.game.explainer.explain(node, adjective, comparison_node, print_context=False, explanation_depth=explanation_depth)

                    # Build explaining_question
                    if isinstance(explanation, Implies):
                        explanation.consequent.build_str_components()
                        verb_str = explanation.consequent.verb_str
                        predicate_str = explanation.consequent.predicate_str
                        
                        object_str = explanation.consequent.object_str
                        if object_str.count("::node::") == 1: # We are simply comparing two nodes
                            object_str = f" {comparison_node.game_tree_node_string} [id: {comparison_node.id}]"                            

                        explaining_question = f"Why {verb_str} {node.game_tree_node_string} [id: {node.id}]{' that' if verb_str != 'is' else ''} {predicate_str}{object_str}?"
                    else:
                        explaining_question = f""
                        
                    explanation = str(explanation)

                    # If we are in interface mode, we need to replace the node references with hyperlinks
                    if activated:
                        LogicalExpression.set_hyperlink_mode(False)

                        # Replace node references with HTML hyperlinks
                        explanation = re.sub(
                            r'::node::\((.*?)\)\[(.*?)\]',
                            lambda m: f'<a href="?node_id={node_id}&adjective={adjective}&show_node_id={m.group(1)}" title="{m.group(1)}" style=" text-decoration: none;"><b style="color: var(--color-accent);">{m.group(2)}</b></a>',
                            explanation
                        )

            if self.explain_in_hyperlink_mode:
                full_return = ExplainerGradioInterface.cool_html_text_container.format(explanation)
            else:
                full_return = f"```markdown\n{explanation}\n```"

            explaining_question = ExplainerGradioInterface.cool_html_text_container.format(explaining_question)

            return full_return, explaining_question

        def visualize_decision_tree(self):
            """Generate a visualization of the Decision Tree."""
            root_node = self.explaining_agent.choice.parent
            try:
                return self.explaining_agent.core.visualize_decision_tree(root_node)
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
        framework = explainer.frameworks['highlevel']
        builder = ExplainerGradioInterface(framework=framework, explanation_depth=3, explaining_agent=None)
        builder.launch()
        #builder.visualize_graph("as next move", debug=True)
        #builder.visualize_graph("as next move")