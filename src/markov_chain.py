'''
We will use tensors for the probabilities in the context of the Markov Chain implementation.
This is why:

1. Preparation for Advanced Operations (e.g. Gradient Computation): If we plan to adjust the transition probabilities in a learning process (e.g., using reinforcement learning or optimization techniques to find optimal transitions), tensors are necessary because they can store gradients. PyTorch automatically computes gradients for tensors during backpropagation, allowing for easy optimization.

2. GPU Acceleration: PyTorch tensors can be moved to a GPU, which significantly speeds up computations involving large arrays of data. If your Markov Chain scales up to handle very large states or transitions, or if you perform many repeated calculations (such as in simulations or probabilistic inferences), using the GPU can provide performance benefits.

3. Unified Data Type: By using tensors throughout your project, especially if it heavily relies on PyTorch for other tasks, you maintain consistency in data types. This consistency can simplify the interface between different parts of your project, reducing the need for data type conversions and potentially decreasing bugs or performance issues.

4. Interoperability: If your Markov Chain is part of a larger system that includes neural networks or other machine learning models built with PyTorch, using tensors ensures that all parts of your system can easily interact. This is particularly relevant when outputs from one part (like a neural network predicting transition probabilities based on state features) are inputs to another (like your Markov Chain).

5. Batch Operations: PyTorch excels at performing batch operations on tensors, which can be advantageous if you're computing transitions for multiple states simultaneously or if you're aggregating results across multiple runs of a stochastic model. Vectorization can lead to code that is not only faster but also more concise and easier to understand.

6. Flexibility for Future Enhancements: Even if your current project scope doesn't require complex operations on the transition probabilities, planning for future enhancements by using tensors allows you to add features later without a major overhaul. For example, you could add features like dynamic adjustment of probabilities, integration with machine learning for adaptive learning rates, or real-time analysis of state transitions.


tl;dr: while using tensors for storing probabilities in a Markov Chain might introduce a bit of overhead for simple scenarios, it offers significant advantages for scalability, performance, and future expansion of your project. It aligns with best practices when using a deep learning framework like PyTorch, preparing your project for potential complexities and integrations.
'''

import warnings
import torch

class MarkovChain:

    class MarkovNode:
        '''MarkovNode objects should be handled through the MarkovChain class.'''
        def __init__(self, name):
            self.name = name
            self.connections = {}  # Maps node to probability tensor
            ''' 
            self.connections maps node instances to probability of transition. 
            e.g.:
            {<src.markov_chain.MarkovNode object at 0x7f54ea37e3e0>: tensor(0.1000)}
            Do not customize the __hash__ of the MarkovNode or you might cause collisions and other problems with the connections dict.
            '''

        def __format_probability(self, probability):
            return torch.tensor(probability)

        def __add_connection(self, node, probability):
            # Adds a connection to another node with a given transition probability
            probability = self.__format_probability(probability)
            self.connections[node] = probability
        
        def check_consistency(self):
            # Checks if probabilities in the node sum up to 1
            if not abs(sum(prob for _, prob in self.connections) - 1) + probability < 1e-6:
                warnings.warn("Probabilities for each node must sum to 1")
                return False


    def __init__(self):
        self.nodes = {}
        ''' 
        self.nodes maps node ids to their instances.
        '''

    @classmethod
    def from_dict(cls, input_dict):
        """
        Class method to create a MarkovChain from a dictionary.
        
        The dictionary should be formatted as follows:
        {
            'NodeName': [('OutboundConnectedNodeName1', probability1), ('OutboundConnectedNodeName2', probability2), ...],
            ...
        }

        Each key represents a node, and its value is a list of tuples where each tuple consists of a target node name
        and the transition probability to that node. The sum of the probabilities for each list should be 1.
        """
        mc = cls()
        for node, connections in input_dict.items():
            mc.add_many_transitions(node, connections)
        return mc
    
    def __add_node(self, node_name):
        # Add a node if it doesn't exist
        if node_name not in self.nodes:
            self.nodes[node_name] = self.MarkovNode(node_name)
        return self.nodes[node_name]

    '''Methods to handle transitions'''
    def add_transition(self, from_node, to_node, probability):
        '''
        Ensures both nodes are in the chain and adds a directed connection.
        Please make sure the connections probabilities add up to 1. 
        '''
        node_from = self.__add_node(from_node)
        node_to = self.__add_node(to_node)
        node_from._MarkovNode__add_connection(node_to, probability)

    def add_many_transitions(self, node, connections):
        """
        Args:
            node (str): The node to which add the connections.
            connections (list of tuples): Outbound connections of the node as tuples: ('OutboundConnectedNodeName1', probability1)
            """
        if not all(isinstance(prob, (float, int)) for _, prob in connections):
            raise ValueError("All probabilities should be numbers")
        if not abs(sum(prob for _, prob in connections) - 1) < 1e-6:
            raise ValueError("Probabilities for each node must sum to 1")
        
        for target_node, probability in connections:
            self.add_transition(node, target_node, probability)

    def get_transition_probability(self, from_node, to_node):
        # Retrieves the transition probability from one node to another
        node_from = self.nodes.get(from_node)
        node_to = self.nodes.get(to_node)
        if node_from and node_to in node_from.connections:
            return node_from.connections[node_to]
        return None

    '''Output methods'''
    def to_dict(self):
        """
        Converts the MarkovChain instance into a dictionary format.

        Returns:
            dict: A dictionary where each key is a node name, and the value is a list of tuples.
                Each tuple contains (connected_node_name, transition_probability) indicating
                the probability of transitioning from the key node to the connected node.
        """
        output_dict = {}
        for node_name, node in self.nodes.items():
            # Collect all connections from the current node along with their probabilities
            connections_list = []
            for connected_node, probability_tensor in node.connections.items():
                # Convert tensor probability back to a Python float for readability and external use
                connections_list.append((connected_node.name, probability_tensor.item()))
            output_dict[node_name] = connections_list
        return output_dict


    def __str__(self):
        result = "Markov Chain States and Probabilities\n"
        for node_name, node in self.nodes.items():
            result += f"\nState: {node_name}\nConnections:\n"
            for connected_node, prob in node.connections.items():
                result += f"{node_name} -> {connected_node.name} with P = {prob.item()}\n"
        return result