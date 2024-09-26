import gradio as gr
import networkx as nx
import matplotlib.pyplot as plt
import io
from PIL import Image
from src.explainer.adjective import BooleanAdjective, PointerAdjective, QuantitativePointerAdjective, ComparisonAdjective
from src.explainer.explanation import Assumption, Possession, Comparison, ConditionalExplanation
import base64
import tempfile

class Node:
    def __init__(self, id, type, adjective):
        self.id = id
        self.type = type
        self.adjective = adjective
        self.explanation = adjective.explanation

class Graph:
    def __init__(self):
        self.nodes = {}
    
    def add_node(self, node):
        self.nodes[node.id] = node
    
    def remove_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]

graph = Graph()

def add_adjective(name, adjective_type, definition, explanation_type, explanation_params):
    if name in graph.nodes:
        return f"Adjective {name} already exists", None, None, None, None, None
    
    if adjective_type == "BooleanAdjective":
        adjective = BooleanAdjective(name, definition)
    elif adjective_type == "PointerAdjective":
        adjective = PointerAdjective(name, definition)
    elif adjective_type == "QuantitativePointerAdjective":
        adjective = QuantitativePointerAdjective(name, definition)
    elif adjective_type == "ComparisonAdjective":
        adjective = ComparisonAdjective(name, definition)
    
    if explanation_type == "Assumption":
        adjective.explanation = Assumption(explanation_params)
    elif explanation_type == "Possession":
        adjective.explanation = Possession(*explanation_params.split(','))
    elif explanation_type == "Comparison":
        adjective.explanation = Comparison(*explanation_params.split(','))
    elif explanation_type == "ConditionalExplanation":
        adjective.explanation = ConditionalExplanation(explanation_params)
    
    node = Node(name, adjective_type, adjective)
    graph.add_node(node)
    return f"Added adjective: {name} with explanation: {type(adjective.explanation).__name__}", "", "", "", "", ""

def add_explanation(name, explanation_type, params):
    if name not in graph.nodes:
        return f"Adjective {name} not found", None, None, None
    
    node = graph.nodes[name]
    if explanation_type == "Assumption":
        node.explanation = Assumption(params)
    elif explanation_type == "Possession":
        node.explanation = Possession(*params.split(','))
    elif explanation_type == "Comparison":
        node.explanation = Comparison(*params.split(','))
    elif explanation_type == "ConditionalExplanation":
        node.explanation = ConditionalExplanation(params)
    
    return f"Added explanation to {name}: {explanation_type}", "", "", ""

def delete_adjective(name):
    if name in graph.nodes:
        graph.remove_node(name)
        return f"Deleted adjective: {name}"
    else:
        return f"Adjective {name} not found"

def delete_explanation(name):
    if name in graph.nodes:
        node = graph.nodes[name]
        node.explanation = None
        return f"Deleted explanation for adjective: {name}"
    else:
        return f"Adjective {name} not found"

def get_adjective_names():
    return list(graph.nodes.keys())

def visualize_graph():
    G = nx.DiGraph()
    
    node_colors = []
    for node_id, node in graph.nodes.items():
        G.add_node(node_id, label=f"{node.id}\n{node.type}")
        node_colors.append('lightblue')
        
        if node.explanation:
            exp_id = f"{node_id}_exp"
            exp_label = f"{type(node.explanation).__name__}"
            G.add_node(exp_id, label=exp_label)
            node_colors.append('lightgreen')
            G.add_edge(node_id, exp_id)
            
            # Connect explanation to other nodes if referenced
            for value in node.explanation.__dict__.values():
                if isinstance(value, str) and value in graph.nodes:
                    G.add_edge(exp_id, value)
    
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.9, iterations=50)
    
    # Draw the graph with arrows
    nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G, 'label'),
            node_color=node_colors, node_size=3000, edge_color='gray', arrows=True, arrowsize=20,
            connectionstyle='arc3,rad=0.1')
    
    plt.axis('off')
    
    # Save the plot to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        plt.savefig(tmp_file.name, format='png', dpi=300, bbox_inches='tight')
    
    plt.close()
    
    return tmp_file.name

def update_dropdowns():
    choices = get_adjective_names()
    return [gr.update(choices=choices, value=None) for _ in range(3)]

with gr.Blocks() as demo:
    gr.Markdown("# X-Tree-Search Explainer Builder")
    
    with gr.Tab("Add Adjective"):
        adj_name = gr.Textbox(label="Adjective Name")
        adj_type = gr.Dropdown(["BooleanAdjective", "PointerAdjective", "QuantitativePointerAdjective", "ComparisonAdjective"], label="Adjective Type")
        adj_definition = gr.Textbox(label="Definition")
        explanation_type = gr.Dropdown(["Assumption", "Possession", "Comparison", "ConditionalExplanation"], label="Explanation Type")
        explanation_params = gr.Textbox(label="Explanation Parameters")
        adj_button = gr.Button("Add Adjective")
        adj_output = gr.Textbox(label="Output")
    
    with gr.Tab("Add/Update Explanation"):
        exp_name = gr.Dropdown(choices=get_adjective_names(), label="Adjective Name", allow_custom_value=True)
        exp_type = gr.Dropdown(["Assumption", "Possession", "Comparison", "ConditionalExplanation"], label="Explanation Type")
        exp_params = gr.Textbox(label="Parameters")
        exp_button = gr.Button("Add/Update Explanation")
        exp_output = gr.Textbox(label="Output")
    
    with gr.Tab("Delete"):
        del_adj_name = gr.Dropdown(choices=get_adjective_names(), label="Adjective Name to Delete", allow_custom_value=True)
        del_adj_button = gr.Button("Delete Adjective")
        del_exp_name = gr.Dropdown(choices=get_adjective_names(), label="Adjective Name to Delete Explanation", allow_custom_value=True)
        del_exp_button = gr.Button("Delete Explanation")
        del_output = gr.Textbox(label="Output")
    
    with gr.Tab("Visualize"):
        visualize_button = gr.Button("Visualize Graph")
        graph_output = gr.Image(label="Graph Visualization")  # Changed to gr.Image

    # Update dropdown choices when adjectives are added or deleted
    adj_button.click(add_adjective, 
                     inputs=[adj_name, adj_type, adj_definition, explanation_type, explanation_params], 
                     outputs=[adj_output, adj_name, adj_type, adj_definition, explanation_type, explanation_params])
    adj_button.click(update_dropdowns, outputs=[exp_name, del_adj_name, del_exp_name])

    exp_button.click(add_explanation, 
                     inputs=[exp_name, exp_type, exp_params], 
                     outputs=[exp_output, exp_name, exp_type, exp_params])

    del_adj_button.click(delete_adjective, inputs=[del_adj_name], outputs=[del_output])
    del_adj_button.click(update_dropdowns, outputs=[exp_name, del_adj_name, del_exp_name])

    del_exp_button.click(delete_explanation, inputs=[del_exp_name], outputs=[del_output])

    visualize_button.click(visualize_graph, inputs=[], outputs=[graph_output])

if __name__ == "__main__":
    demo.launch()