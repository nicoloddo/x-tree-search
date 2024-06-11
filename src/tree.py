from src.markov_chain import MarkovChain

class Tree(MarkovChain):
    """
    Manages the tree structure including the root and the ability to expand the tree from each node.
    The nodes names are ids that refer to the path needed to reach them.
    The root node has id=0.
    A subsequent node would be for example:
    "0102" which means that to get there you need: root.children[1].children[0].children[2]
    """
    class TreeNode(MarkovChain.MarkovNode):
        """
        Represents a single node in a tree.

        Attributes:
            parent (TreeNode): The TreeNode parent of this node. If it is None, this is the root node, identified with the id:"0".
            children (list): A list of Node instances that are the children of this node.
            is_leaf (bool): Indicates whether this node is a leaf of the tree.
        """
        def __init__(self, parent, value):
            self.parent = parent
            self.value = value    
            self.is_leaf = True

            if parent == None:
                name = "0"
            else:
                name = parent.name + str(len(parent.children))

            super().__init__(name)
        
        def __add_child(self, child, probability):
            self._MarkovNode__add_connection(child, probability)
            if len(self.connections) > 0:
                self.is_leaf = False
        
        @property
        def children_and_probs(self):
            """Returns a list of tuples containing children of this node and the respective transition probability"""
            return self.connections.items()

        @property
        def children(self):
            """Returns a list of children nodes of this node"""
            return [t[0] for t in self.children_and_probs] # Extract the first item of the tuple, which is the pointer to the child node
    

    def __init__(self):
        super().__init__()
        self.root = self.__add_node() # Add root node

    def __add_node(self, parent=None, value=0):
        """Overrides the add_node method to ensure TreeNode objects are created."""
        new_node = self.TreeNode(parent, value)
        self.nodes[new_node.name] = new_node
        return new_node

    def set_children(self, node_id, children_values):
        """
        Expands a node with a given amount of children and their values

        Args:
            node (str): The id of the node to expand with new children.
            children_values (list of numbers): Values to assign to the children nodes.
        """
        parent = self.nodes[node_id]
        for value in children_values:
            child = self.__add_node(parent=parent, value=value)
            probability = 1/len(children_values)
            parent._TreeNode__add_child(child, probability)

    def get_node(self, node_id):
        """
        Returns a node given its id.

        Args:
            node (str): The id of the node to get.
        """
        return self.nodes[node_id]

    def __str__(self):
        result = "Tree\n"
        for node_id, node in self.nodes.items():
            result += f"\nNode: {node_id}\nChildren:\n"
            for child, prob in node.children_and_probs:
                result += f"{child.name} with P = {prob.item()} and value V = {child.value}\n" # remember that prob is a tensor
        return result



        

