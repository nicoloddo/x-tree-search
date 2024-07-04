from src.structures.markov_chain import MarkovChain

class Tree(MarkovChain):
    """
    Manages the tree structure including the root and the ability to expand the tree from each node.
    The nodes names are ids that refer to the path needed to reach them.
    The root node has id=0.
    A subsequent node would be for example:
    "0102" which means that to get there you need: root.children[1].children[0].children[2]
    """
    def __init__(self):
        super().__init__()
        self.root = self.__add_node() # Add root node

    class TreeNode(MarkovChain.MarkovNode):
        """
        Represents a single node in a tree.

        Attributes:
            parent (TreeNode): The TreeNode parent of this node. If it is None, this is the root node, identified with the id:"0".
            is_leaf (bool): Indicates whether this node is a leaf of the tree.
            value (object): Any object can be assigned to a node value.
            children (list) (derived): A list of Node instances that are the children of this node (derived property from the original MarkovNode.connections attribute)
            children_and_probs (list) (derived): List of tuples containing children of this node and the respective transition probability
        """
        def __init__(self, parent, value):
            self.parent = parent
            self.value = value    
            self.is_leaf = True

            if parent == None:
                node_id = "0"
            else:
                node_id = parent.id + '_' + str(len(parent.children))

            super().__init__(node_id)
        
        def _add_child(self, child, probability):
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

        @property
        def id(self):
            return self.name

        @id.setter
        def id(self, value):
            self.name = value

    def __add_node(self, parent=None, value=None):
        """Overrides the add_node method to ensure TreeNode objects are created."""
        new_node = self.TreeNode(parent, value)
        self.nodes[new_node.id] = new_node
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
            parent._add_child(child, probability)

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
                result += f"{child.id} with P = {prob.item()} and value V = {child.value}\n" # remember that prob is a tensor
        return result



        

