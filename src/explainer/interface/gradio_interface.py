from typing import Dict
import gradio as gr
import tempfile
import inspect
import sys
import graphviz
import re
from urllib.parse import urlencode

from src.explainer.adjective import Adjective
from src.explainer.explanation import Explanation, Assumption, CompositeExplanation, ConditionalExplanation
from src.explainer.framework import ArgumentationFramework
from src.explainer.propositional_logic import LogicalExpression

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
    def __init__(self, *, game=None, explanation_depth=2, framework=None, explaining_agent, explain_in_hyperlink_mode=True):
        """Initialize the ExplainerInterface with an optional game to explain.
        
        :param game: The game to explain.
        :param explanation_depth: The depth of the explanation.
        :param framework: The framework to use. Only provide if game is not provided.
        :param explaining_agent: The agent that explains its choices.
        """
        self.game = game
        if self.game:
            if framework:
                raise ValueError("Framework must be provided only if game is not provided.")
            self.framework = self.game.explainer.framework or ArgumentationFramework(refer_to_nodes_as="node")
        else:
            self.framework = framework or ArgumentationFramework(refer_to_nodes_as="node")
        self.explaining_agent = explaining_agent
        self.explain_in_hyperlink_mode = explain_in_hyperlink_mode

        self.nodes = {}
        self.demo = gr.Blocks()
        self.build_interface()
        self.load_framework()
        self.explanation_depth = explanation_depth

    def load_framework(self):
        """Load the adjectives from the framework."""
        for adjective in self.framework.adjectives.values():
            self._add_adjective(adjective)

    def _add_adjective(self, adjective):
        """Add an adjective to the graph."""
        node = Node(adjective.name, type(adjective).__name__, adjective)
        self.nodes[node.id] = node

    def add_adjective(self, name, adjective_type, definition, explanation_type, explanation_params):
        """Add a new adjective with optional explanation to the graph and framework."""
        if name in self.nodes:
            return f"Adjective {name} already exists", None, None, None, None, None
        
        # Create adjective
        adjective = adjective_classes.get(adjective_type, lambda *args: None)(name, definition)
        if not adjective:
            return f"Adjective type {adjective_type} not found", None, None, None, None, None
        
        # Create explanation
        if explanation_type:
            explanation_class = explanation_classes.get(explanation_type)
            if not explanation_class:
                return f"Explanation type {explanation_type} not found", None, None, None, None, None
            params = [explanation_params] if explanation_type == "Assumption" else explanation_params.split(',')
            adjective.explanation = explanation_class(*params)
        
        self._add_adjective(adjective)
        self.framework.add_adjective(adjective)
        return f"Added adjective: {name} with explanation: {type(adjective.explanation).__name__}", "", "", "", "", ""

    def add_explanation(self, name, explanation_type, params):
        """Add or update an explanation for an existing adjective."""
        if name not in self.nodes:
            return f"Adjective {name} not found", None, None, None, None
        
        adjective = self.nodes[name].adjective
        explanation_class = explanation_classes.get(explanation_type)
        if not explanation_class:
            return f"Explanation type {explanation_type} not found", None, None, None, None
        
        params = [params] if explanation_type == "Assumption" else params.split(',')
        adjective.explanation = explanation_class(*params)
        
        return f"Added explanation to {name}: {explanation_type}", "", "", "", ""

    def delete_adjective(self, name):
        """Delete an adjective from the graph and framework."""
        if name in self.nodes:
            del self.nodes[name]
            self.framework.del_adjective(name)
            return f"Deleted adjective: {name}"
        return f"Adjective {name} not found"

    def delete_explanation(self, name):
        """Delete the explanation of an adjective."""
        if name in self.nodes:
            self.nodes[name].explanation = None
            return f"Deleted explanation for adjective: {name}"
        return f"Adjective {name} not found"

    def get_adjective_names(self):
        """Get a list of all adjective names in the graph."""
        return list(self.nodes.keys())

    def visualize_graph(self, root_adjective=None, debug=False):
        """Generate a visualization of the subgraph starting from the given root adjective."""
        if root_adjective:
            if root_adjective not in self.nodes:
                return None

        # Create a new directed graph
        dot = graphviz.Digraph(comment='Explanation Flowchart')
        dot.attr(rankdir='LR')  # Left to Right layout
        dot.attr('node', shape='rectangle', style='rounded,filled', fontname='Arial', fontsize='10')
        dot.attr('edge', fontname='Arial', fontsize='8')

        processed_nodes = set()

        def process_node(node_id, *, parent_id = None, explanation_depth=0, is_root=False):
            """Process a node and its explanation, adding them to the graph."""
            explanation_depth += 1
            node = self.nodes[node_id]

            def already_in_nodes(node_id):
                if node_id in processed_nodes:
                    suffix = 1
                    while f"{node_id}_copy{suffix}" in processed_nodes:
                        suffix += 1
                    new_id = f"{node_id}_copy{suffix}"
                    return True, new_id
                return False, node_id

            is_duplicate, node_id = already_in_nodes(node_id)

            label = f"{node.id}\n{node.type}"
            color = 'purple' if is_root else 'lightblue'
            dot.node(node_id, label, fillcolor=color)
            if parent_id:
                dot.edge(parent_id, node_id)
            processed_nodes.add(node_id)

            if explanation_depth >= self.explanation_depth:
                return
            
            if (not is_duplicate or is_root) and node.explanation:
                process_explanation(node_id, node.explanation, f"{node_id}_exp", explanation_depth=explanation_depth)

        def process_explanation(parent_id, explanation, exp_id, edge_label=None, *, explanation_depth=0):
            """Process an explanation, adding it and its components to the graph."""
            exp_label = type(explanation).__name__

            if isinstance(explanation, Assumption):
                dot.node(exp_id, f"{exp_label}\n{explanation.description}", fillcolor='lightgreen')
                dot.edge(parent_id, exp_id, label=edge_label)

            elif isinstance(explanation, CompositeExplanation):
                dot.node(exp_id, exp_label, fillcolor='darkgreen')
                dot.edge(parent_id, exp_id, label=edge_label)
                for i, sub_exp in enumerate(explanation.explanations):
                    process_explanation(exp_id, sub_exp, f"{exp_id}_sub_{i}", explanation_depth=explanation_depth)

            elif isinstance(explanation, ConditionalExplanation):
                condition_id = f"{exp_id}_condition"
                dot.node(condition_id, f"If\n{explanation.condition.adjective_name}", fillcolor='yellow')
                dot.edge(parent_id, condition_id, label=edge_label)

                process_explanation(condition_id, explanation.explanation_if_true, f"{exp_id}_true", 'True', explanation_depth=explanation_depth)
                process_explanation(condition_id, explanation.explanation_if_false, f"{exp_id}_false", 'False', explanation_depth=explanation_depth)

            else:
                dot.node(exp_id, exp_label, fillcolor='lightgreen')
                dot.edge(parent_id, exp_id, label=edge_label)
                for key, value in explanation.__dict__.items():
                    if key == "explanation_of_adjective":
                        continue
                    if isinstance(value, str) and value in self.get_adjective_names():
                        process_node(value, parent_id=exp_id, explanation_depth=explanation_depth)

        if root_adjective:
            process_node(root_adjective, is_root=True)
        else: # Visualize all adjectives
            prev_explanation_depth = self.explanation_depth
            self.explanation_depth = float('inf')
            processed_nodes = set(self.nodes.keys())
            for node_id in self.nodes:
                process_node(node_id, is_root=True)
            self.explanation_depth = prev_explanation_depth

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            # Get the name of the temporary file
            tmp_filename = tmp_file.name

        # Render the graph to the temporary file
        dot.attr(dpi='300')  # dpi resolution (300 is generally good for high resolution)
        dot.render(tmp_filename, format='png', cleanup=True)

        # The rendered file will have '.png' appended to it
        rendered_filename = tmp_filename + '.png'

        # For debugging: Display the image
        if debug:
            import matplotlib.pyplot as plt
            import matplotlib.image as mpimg

            img = mpimg.imread(rendered_filename)
            plt.figure(figsize=(20, 20))
            plt.imshow(img)
            plt.axis('off')
            plt.show()

        # Return the path to the temporary PNG file
        return rendered_filename

    def update_dropdowns(self):
        """Update all dropdowns with current adjective names."""
        choices = self.get_adjective_names()
        return [gr.update(choices=choices, value=None) for _ in range(4)]
    
    def update_ai_explanation(self, node_id=None, adjective="the best"):
        """
        Update the AI explanation.

        :param node_id: The ID of the node to explain.
        :param adjective: The adjective to use in the explanation.
        """
        code_markdown_block = not self.explain_in_hyperlink_mode
        template = "```markdown\n{explanation}\n```" if code_markdown_block else "{explanation}"

        if not self.game:
            return template.format(explanation="No game was provided.")
        else:
            if self.explaining_agent is None:
                return template.format(explanation="No explaining agent was found.")
            
            if node_id is None:
                node = self.explaining_agent.choice
            else:
                node = self.explaining_agent.core.nodes[node_id]
            if node is None:
                return template.format(explanation="No node was found.")
            
            # All is good, we can explain
            if self.explain_in_hyperlink_mode:
                activated = LogicalExpression.set_hyperlink_mode(self.explain_in_hyperlink_mode, node.__class__)
            else:
                activated = False

            explanation = self.game.explainer.explain(node, adjective)

            # If we are in interface mode, we need to replace the node references with hyperlinks
            if activated:
                LogicalExpression.set_hyperlink_mode(False)

                # Replace node references with Markdown hyperlinks
                explanation = re.sub(
                    r'::node::\((.*?)\)\[(.*?)\]',
                    lambda m: f'[{m.group(2)}](#{m.group(1)})',
                    explanation
                )

            return template.format(explanation=explanation)

    def update_game_state_display(self, node_id, request: gr.Request):
        """
        Update the game state display.

        :param node_id: The ID of the node to display.
        :param request: The Gradio Request object.
        """
        if request:
            query_params = dict(request.query_params)
            if 'node_id' in query_params:
                node_id = query_params['node_id']

        node = self.explaining_agent.core.nodes[node_id]
        return f"Showing: {node.id}\n{node.state}"

    #-----------------------------------------------------------------------------------------------------------
    """INTERFACE BUILDER METHODS"""
    def build_ai_explanation_tab(self, tab_label: str = "Explain", toggles: Dict[str, tuple[str, bool]] = None):
        """
        Build the AI explanation tab.

        :param tab_label: The label of the tab.
        :param toggles: A dictionary of toggles to add to the interface. 
        The key is the name of the toggle, the value is a tuple of the label and the value.
        """
        with gr.Tab(tab_label):
            if self.explain_in_hyperlink_mode:
                with gr.Row():
                    with gr.Column(scale=1):
                        id_input = gr.Textbox(label="Node ID")
                        ai_exp_adj_name = gr.Dropdown(choices=self.get_adjective_names(), label="Adjective")
                        explain_button = gr.Button("Explain")
                    
                    with gr.Column(scale=2):
                        game_state_display = gr.Markdown(value="Showing: None", label="Game State")

            gr.Markdown("# AI Move Explanation")
            explanation_output = gr.Markdown(value=self.update_ai_explanation(), label="AI move explanation")
            new_toggles = {}
            if toggles:
                for name, toggle_params in toggles.items():
                    label, value = toggle_params
                    new_toggles[name] = gr.Checkbox(label=label, value=value)

        components = {
            "explanation_output": explanation_output,
            **new_toggles
        }
        
        if self.explain_in_hyperlink_mode:
            components.update({
                "id_input": id_input,
                "ai_exp_adj_name": ai_exp_adj_name,
                "explain_button": explain_button,
                "game_state_display": game_state_display,
            })
        
        return components

    def build_add_adjective_tab(self, tab_label: str = "Add Adjective"):
        """
        Build the add adjective tab.

        :param tab_label: The label of the tab.
        """
        with gr.Tab(tab_label):
            adj_name = gr.Textbox(label="Adjective Name")
            adj_type = gr.Dropdown(list(adjective_classes.keys()), label="Adjective Type")
            adj_definition = gr.Textbox(label="Definition")
            explanation_type = gr.Dropdown(list(explanation_classes.keys()), label="Explanation Type")
            explanation_params = gr.Textbox(label="Explanation Parameters")
            adj_button = gr.Button("Add Adjective")
            adj_output = gr.Textbox(label="Output")

        return {
            "adj_name": adj_name,
            "adj_type": adj_type,
            "adj_definition": adj_definition,
            "explanation_type": explanation_type,
            "explanation_params": explanation_params,
            "adj_button": adj_button,
            "adj_output": adj_output
        }

    def build_add_update_explanation_tab(self, tab_label: str = "Add/Update Explanation"):
        """
        Build the add/update explanation tab.
        TODO: The CompositeExplanation and ConditionalExplanations need to be handled differently

        :param tab_label: The label of the tab.
        """
        # TODO: The CompositeExplanation and ConditionalExplanations need to be handled differently
        with gr.Tab(tab_label):
            exp_adj_name = gr.Dropdown(choices=self.get_adjective_names(), label="Adjective Name", allow_custom_value=True)
            exp_type = gr.Dropdown(list(explanation_classes.keys()), label="Explanation Type")
            exp_params = gr.Textbox(label="Parameters")
            exp_button = gr.Button("Add/Update Explanation")
            exp_output = gr.Textbox(label="Output")

        return {
            "exp_adj_name": exp_adj_name,
            "exp_type": exp_type,
            "exp_params": exp_params,
            "exp_button": exp_button,
            "exp_output": exp_output
        }

    def build_delete_tab(self, tab_label: str = "Delete Adjective"):
        """
        Build the delete tab.

        :param tab_label: The label of the tab.
        """
        with gr.Tab(tab_label):
            del_adj_name = gr.Dropdown(choices=self.get_adjective_names(), label="Adjective Name to Delete", allow_custom_value=True)
            del_adj_button = gr.Button("Delete Adjective")
            del_output = gr.Textbox(label="Output")

        return {
            "del_adj_name": del_adj_name,
            "del_adj_button": del_adj_button,
            "del_output": del_output
        }

    def build_visualize_tab(self, tab_label: str = "Visualize"):
        """
        Build the visualize tab.

        :param tab_label: The label of the tab.
        """
        with gr.Tab(tab_label):
            root_adjective = gr.Dropdown(choices=self.get_adjective_names(), label="Select Root Adjective (optional)")
            visualize_button = gr.Button("Visualize Framework")
            graph_output = gr.Image(label="Graph Visualization")

        return {
            "root_adjective": root_adjective,
            "visualize_button": visualize_button,
            "graph_output": graph_output
        }

    def connect_components(self, components):
        """
        Connect the components of the interface.

        :param components: The components to connect.
        """
        # Explain
        if "explain_button" in components:
            components["explain_button"].click(
                self.update_ai_explanation,
                inputs=[components["id_input"], components["ai_exp_adj_name"]],
                outputs=[components["explanation_output"]]
            )            

        # Add Adjective
        if "adj_button" in components:
            components["adj_button"].click(
                self.add_adjective, 
                inputs=[components["adj_name"], components["adj_type"], components["adj_definition"], 
                        components["explanation_type"], components["explanation_params"]], 
                outputs=[components["adj_output"], components["adj_name"], components["adj_type"], 
                         components["adj_definition"], components["explanation_type"], components["explanation_params"]]
            )

        # Add/Update Explanation
        if "exp_button" in components:
            components["exp_button"].click(
                self.add_explanation, 
                inputs=[components["exp_adj_name"], components["exp_type"], components["exp_params"]], 
                outputs=[components["exp_output"], components["exp_adj_name"], components["exp_type"], components["exp_params"]]
            )

        # Delete Adjective
        if "del_adj_button" in components:
            components["del_adj_button"].click(
                self.delete_adjective, 
                inputs=[components["del_adj_name"]], 
                outputs=[components["del_output"]]
            )

        # Visualize
        if "visualize_button" in components:
            components["visualize_button"].click(
                self.visualize_graph, 
                inputs=[components["root_adjective"]], 
                outputs=[components["graph_output"]]
            )

        # Update dropdowns
        dropdown_components = [comp for comp in [components.get("exp_adj_name"), components.get("del_adj_name"), 
                                                 components.get("root_adjective"), components.get("ai_exp_adj_name")] if comp is not None]
        if dropdown_components:
            for button in [components.get("adj_button"), components.get("del_adj_button")]:
                if button:
                    button.click(self.update_dropdowns, outputs=dropdown_components)

    def build_interface(self):
        with gr.Blocks() as demo:
            gr.Markdown("# X-Tree-Search Explainer")
            
            with gr.Tabs():
                ai_explanation_components = self.build_ai_explanation_tab()
                add_adj_components = self.build_add_adjective_tab()
                add_exp_components = self.build_add_update_explanation_tab()
                delete_components = self.build_delete_tab()
                visualize_components = self.build_visualize_tab()

            components = {**ai_explanation_components, **add_adj_components, **add_exp_components, **delete_components, **visualize_components}

            # Connect components
            self.connect_components(components)

        return demo

    def launch(self):
        """Launch the Gradio interface."""
        self.demo = self.build_interface()
        self.demo.launch()

if __name__ == "__main__":
    from explainers.alphabeta_explainer import AlphaBetaExplainer
    explainer = AlphaBetaExplainer()
    framework = explainer.frameworks['highlevel']
    builder = ExplainerGradioInterface(framework=framework, explanation_depth=3, explaining_agent=None)
    builder.launch()
    #builder.visualize_graph("as next move", debug=True)
    #builder.visualize_graph("as next move")