MAX_ENVIRONMENT_SIZE_TO_PRINT = 30

from common.utils import join_arrays_respective_elements

import numpy as np
import inspect
import copy

class GameModel:
    def __init__(self, agents_number, default_agent_features, additional_agent_features, agent_features_descriptions="No description was given.", game_name=""):
        """
        Initializes the GameModel. You need to define the agent features only.
        The GameModel utilizes Action Spaces: spaces on which actions can be performed, such as a board in tic-tac-toe. 
        Elements or "slots" of action spaces can be modified.
        The agents variable refer as well to a modifiable Action Space, allowing agents to perform actions on other agents and modify their features.
        The game model then allows to define rules. Rules constrain the Action Spaces by limiting the possible actions to perform on them.

        Args:
            
            agents_number(int): Amount of agents that play the game.
            default_agent_features (list of str)): The default features of each agent.
            additional_agent_features (list of list of strings): For each agent feature, specify other possible labels that can be assigned to each.

            agent_features_descriptions (str): Strings explaining each feature of the agents (optional)
            game_name (str): String with the name of the game (optional)

        Attributes:
            game_name (str): String with the name of the game (optional)
            action_spaces (dictionary of ActionSpaces): Dictionary containing the spaces where is possible to perform actions, identifiable by their id. An example would be a 2x2 board.
            rules (dictionary of lists): For each Action Space id, a list of rules, where each rule is a function that takes (who, where, what, game) and returns a bool, True if the rule is broken.
            agents (ActionSpace): A matrix representing the agents and their features, initialized with the default labels, it directly refers to the action_space of the agents.
            
        """
        self.game_name = game_name

        self.rules = {"general": []} # A dictionary of rules divided by action_space ids. General rules are saved in "general"

        self.action_spaces = {} # Dictionary containing the spaces where is possible to perform actions. An example would be a 2x2 board.
        # See the documentation of add_action_space() to add action spaces.

        self.actions = [] # List of actions performed.

        self.started = False # Boolean that keeps track of if the game has started (actions > 0)
        self.ended = False # Boolean that keeps track of if the game has ended

        ''' DEFAULT FEATURES OF EVERY GAME: '''

        ''' Default action spaces: '''
        # Initialize the agents matrix with the default labels
        agents_dimensions = [agents_number, len(default_agent_features)]
        self.add_action_space('agent', agents_dimensions, default_agent_features, additional_labels=additional_agent_features, dimensions_descriptions=agent_features_descriptions)
        self.agents = self.action_spaces['agent']

        ''' Default endgame dynamics'''
        self.endgame_dynamics = lambda: False # This function is checked after every action, if it returns True, the self.ended is changed to True

        ''' Default rule: '''
        self.action_is_violation_if(lambda who, where, what, game: game.ended, "general", rule_description="Nothing is allowed if the game is ended.") # Default rule


        print(f"""
        You can add spaces on which to perform actions with the function add_action_space(dimensions, default_labels, additional_labels, dimensions_description).
        Examples of that are the environment space (or board) and the agent space, which are by default already there.

        You can use the method gm.action_is_violation_if(rule, rule_description) to express rules for the game.\n
        Use help(gm.action_is_violation_if) for help on how to define rules.
        The rule: "Nothing is allowed if the game is ended." is defined by default, to delete it use gm.delete_rule(1).
        Use gm.print_rules() to see all the rules that have been setted.
        
        Use gm.set_endgame(callable_function(game)) to define based on what dynamics your game should end.
        The callable function should have one only input parameter, which represents the game itself, 
        which can be used to refer to anything inside its model, this include:
                - action_spaces = the action spaces belonging to the game, incuding any added one and their features
                - agents = the agents involved in the game and their features
                - actions = previous actions performed
                - started = if the game has started
                - ended = if the game has ended
        Example: 
            def three_elements_in_row(game):
                board = game.action_spaces["board"]
                # Check rows for winning condition
                for row in board:
                    if row[0] == row[1] == row[2] != 'free':
                        return True
                # If no winner, return False
                return False
        \n""")

    ''' Actions spaces'''
    def add_action_space(self, action_space_id, dimensions, default_labels, additional_labels, dimensions_descriptions="No description was given."):
        """
        Attributes:
            dimensions (list of int): The shape of the matrix of the action space.
            default_label (list of str): The default labels to assign to each column in the environment.
            additional_labels (list of list of str): For each provided default_label, provide a list of other possible labels that can be assigned to the environment elements.
        """
        try:
            labels = join_arrays_respective_elements(default_labels, additional_labels)
        except ValueError:
            raise ValueError("You should specify an alternative label for each default label.")

        # Initialize the environment matrix with the default labels
        self.action_spaces[action_space_id] = ActionSpace(dimensions, default_labels, available_labels=labels, dimensions_descriptions=dimensions_descriptions)
        self.rules[action_space_id] = [] # Initialize the array of rules to apply to the action space

    @property
    def printable_action_spaces(self):
        to_print = "Action Spaces:\n\n"
        i=1
        for action_space_id, action_space in self.action_spaces.items():
            to_print += f"{i}. {action_space_id} ({'actions allowed' if action_space.actions_enabled else 'actions disabled'}): \n"
            to_print += f"{action_space.shape}, Number of elements: {action_space.size} \nAvailable labels: {action_space.available_labels})\n\n"
            to_print += f"Dimensions descriptions: {action_space.dimensions_descriptions}\n\n"

            to_print += f"{action_space_id}: \n{action_space}\n\n"
            i+=1

        return to_print

    def delete_action_space(self, action_space_id):
        del self.action_spaces[action_space_id]

    def enable_actions(self, on):
        """ Enables action in a given action space.
            Attributes:
                on : the action_space_id on which to enable actions.
        """

        self.action_spaces[on].actions_enabled = True
    
    def disable_actions(self, on):
        """ Disables action in a given action space.
            Attributes:
                on : the action_space_id on which to disable actions.
        """
        self.action_spaces[on].actions_enabled = False

    ''' Actions dynamics'''
    def action(self, action_space_id, who, where, what):
        """
        Executes an action within the given action_space, modifying its state if the action does not break any rules.

        Args:
            who (int): Identifier (index) for the entity performing the action as index of the respective row in the agents matrix
            where (list/tuple): Location or coordinates in the environment where the action takes place.
            what (str): The action or change being proposed.
            action_space_id (str): The id of the action space on which perform the action.

        Returns:
            False if the action breaks any rules; otherwise, returns the action.
        """
        if self.__break_rules(who, where, what, action_space_id):
            print("This action is not permitted.\n")
            return False
        else:
            action_space = self.action_spaces[action_space_id]
            what_before = self.__apply_action(action_space, where, what)
            return self.__action_performed({'who':who, 'where':where, 'what':what, 'what_before':what_before, 'on':action_space_id})
            
    def __action_performed(self, action):
        self.actions.append(action)
        self.check_started()
        self.check_ended()
        return action

    def __apply_action(self, action_space, where, what):
        if not any(what in sublist for sublist in action_space.available_labels):
            raise ValueError("Actions can only be done with the labels available to the given action space.")
        what_before = action_space[tuple(where)]
        action_space[tuple(where)] = what
        return what_before
    
    def theoretical_unapply_actions(self, actions_to_reverse_amount):
        ''' 
        Unapplies actions in reverse order of execution but does not actually reverse the action space environment.

        return: a dict containing the action_spaces at the state before the actions where performed, with as keys the action_spaces respective ids.
        '''
        previous_action_spaces = {}

        for i in range(1, actions_to_reverse_amount):

            who = self.actions[-i]['who']
            where = self.actions[-i]['where']
            what = self.actions[-i]['what_before']
            action_space_id = self.actions[-i]['on']
            action_space = self.action_spaces[action_space_id]

            if action_space_id not in previous_action_spaces:
                theoretical_action_space = copy.deepcopy(action_space)
                previous_action_spaces[action_space_id] = theoretical_action_space
            
            previous_action_spaces[action_space_id][tuple(where)] = what
        
        return previous_action_spaces


    ''' Rules definition'''
    def action_is_violation_if(self, rule, action_space_id = "general", *, rule_description): # Any argument assigned to parameters after the asterisk * can only be passed as keyword (named) arguments.
        """
        Adds a new rule to the game model after validating the rule's signature and a test run to ensure it returns a boolean.

        Args:
            rule (callable): a previously defined function that returns True if your rule is violated.
            action_space_id: The id of the action space to constrain with the rule. It refers to the matrix onto which the action is being performed, for example actions that modify the environment or the agents matrixes. 
                             If the action is more general, you can leave the parameter blank, it will be assigned to the general rules.
            rule_description (str): a description for the rule.

        Definition of the rule:            
        - The rule has to have as input parameters exactly these 4: who, where, what, game
        - The rule has to return a bool which is True if the rule is violated. You can use a conditional as rule body.
        - The rule has to follow a specific formalism, with variable inside its body referring to:
            1. who = the index of the agent making the action. To refer to the features, use game.agents[who][feature, e.g. 1]
            2. where = the position in the action space to apply the action to (as coordinates)
            3. what = the modification to apply (which should take the value of one of the declared labels and agents_labels)

            4. game = the GameModel, which can be used to refer to anything inside its model, this include:
                - environment = the environment or board
                - agents = the agents involved in the game
                - actions = previous actions performed, which include:
                         {'who': index of the agent performing the action, 'where':coordinates of the action, 'what':value to write in the element, 'what_before':previous value of the element, 'on':action_space_id where action took place}
                - started = if the game has started
                - ended = if the game has ended
        - The 'where' are treated as iterables: to compare them with a None value you should use [None]

        Examples:
        1.  Rule: Only the player whose starter can play the first turn.

            who = the agent who did the action
            agent[0] refers to the agent's first feature, which we assigned to the status
            
            Rule definition:
            gm.action_is_violation_if(lambda who, where, what, game: not game.started and who[0] != 'starter', rule_description="This is not the starting player and this is the first turn.") 
        
        2.  Rule: You can only put a sign if the space is free:

            Rule definition:
            mgm.action_is_violation_if(lambda who, where, what, game: where != 'free', "environment", rule_description="The space needs to be free to put a sign on it.")
        
        
        3.  Rule: Agents cannot modify their features or the ones of other agents:

            Rule definition:
            mgm.action_is_violation_if(lambda who, where, what, game: where != [None], "agent", rule_description="Agents cannot modify their own features.")
        """
        # Validate that the rule is a callable with the correct signature
        if not callable(rule):
            raise ValueError("The rule must be a callable function.")

        # Check the signature of the callable to ensure it has exactly four parameters
        sig = inspect.signature(rule)
        if len(sig.parameters) != 4:
            raise ValueError("Rule function must accept exactly these arguments: who, where, what, game")

        if action_space_id == "general":
            wrapped = lambda who, where, what: self.__wrapped_rule(rule, who, None, what, None)
        else:
            action_space = self.action_spaces[action_space_id]
            wrapped = lambda who, where, what: self.__wrapped_rule(rule, who, action_space[tuple(where)], what, action_space)

        self.rules[action_space_id].append({'description':rule_description, 'broken':wrapped})
    
    def __wrapped_rule(self, rule, who, where, what, action_space):
        return rule(who, where, what, self)
    
    def __break_rules(self, who, where, what, action_space_id):
        """
        Checks all rules based on the given parameters.

        Args:
            who (int): Identifier for the entity performing the action as index of the respective row in the agents matrix
            where (list/tuple): Location or coordinates in the action_space where the action takes place.
            what (str): The action or change being proposed.

        Returns:
            bool: Returns True if any rule is violated, otherwise False.
        """
        action_space = self.action_spaces[action_space_id]
        if not action_space.actions_enabled: # First check if actions are allowed in the space
            print("Actions are not allowed in this Action Space.")
            return True

        # If they are allowed check rules on the action space
        try:
            for i, rule in enumerate(self.rules["general"]): # Check general rules
                if rule['broken'](who, where, what):
                    print("Broke general rule " + str(i+1) + ': ' + rule['description'])
                    return True

            for i, rule in enumerate(self.rules[action_space_id]): # Check rules specific to that action space
                if rule['broken'](who, where, what):
                    print("Broke rule " + str(i+1) + ': ' + rule['description'])
                    return True

        except Exception as e:
            # Log the error and possibly re-raise or handle it as necessary
            raise e
    
    @property
    def printable_rules(self):
        to_print = "Rules:\n\n"
        for action_space_id, action_space_rules in self.rules.items():
            i = 1
            to_print += f"{action_space_id}:\n"
            for rule in action_space_rules:
                to_print += f"{str(i)}: {rule['description']}\n"
                i += 1
            to_print += "\n"
        return to_print

    def delete_rule(self, action_space_id, index):
        del self.rules[action_space_id][index - 1]

    ''' Endgame dynamics setting '''
    def set_endgame(self, callable_function):
        """
        The callable function should have one only input parameter, which represents the game itself, 
        which can be used to refer to anything inside its model, this include:
                - environment = the environment or board (e.g. game.environment)
                - agents = the agents involved in the game
                - actions = previous actions performed
                - started = if the game has started
                - ended = if the game has ended
        Example: 
            def three_elements_in_row(game):
                board = game.action_spaces['board']
                # Check rows for winning condition
                for row in board:
                    if row[0] == row[1] == row[2] != 'free':
                        return True
                # If no winner, return False
                return False
        """
        # Validate that the rule is a callable with the correct signature
        if not callable(callable_function):
            raise ValueError("The end game function must be a callable function.")

        # Check the signature of the callable to ensure it has exactly four parameters
        sig = inspect.signature(callable_function)
        if len(sig.parameters) != 1:
            raise ValueError("The end game function must accept exactly one argument: game")

        self.endgame_dynamics = callable_function

    ''' Checks functions '''
    def check_started(self):
        if len(self.actions) > 0 and not self.started:
            self.started = True
    
    def check_ended(self):
        if self.endgame_dynamics(self):
            self.ended = True


    def __str__(self):
        """
        Provides a string representation of the game model's environment for easy viewing.

        Returns:
            str: A formatted string of the environment matrix.
        """
        to_return = f"Game: {self.game_name}\n\n"

        to_return += self.printable_action_spaces

        '''
        to_return = f"Number of agents: {self.agents.shape[0]}, Number of agent features: {self.agents.shape[1]} \nAgent features labels: {self.agents.available_labels})\n\n"
        to_return += f"Agent features descriptions: {self.agents.dimensions_descriptions}\n\n"

        to_return += f"Agents: \n{self.agents}\n\n"

        for action_space_id, action_space in self.action_spaces.items():
            if action_space_id == 'agent': # skip the agent since we already printed it.
                continue
            to_return += f"{action_space_id} ({'actions allowed' if action_space.actions_enabled else 'actions disabled'}): "
            to_return += f"{action_space.shape}, Number of elements: {action_space.size} \nAvailable labels: {action_space.available_labels})\n\n"
            to_return += f"Dimensions descriptions: {action_space.dimensions_descriptions}\n\n"

            to_return += f"{action_space_id}: \n{action_space}\n"
        '''

        return to_return

class ActionSpace(np.ndarray):
    def __new__(cls, dimensions, default_labels, available_labels, dimensions_descriptions, numpy_matrix=None, *, enable_actions = True):
        """
        Create a numpy array with the given dimensions and default values for each row.
        
        Parameters:
        dimensions (list): List of integers indicating the shape of the numpy array.
        default_labels (list): List of default values for each row.
        available_labels (list): List of available labels.
        dimensions_descriptions (list): Descriptions for each dimension.
        enable_actions (bool): Flag to enable or disable actions.
        
        Returns:
        ActionSpace: An enhanced numpy array with additional attributes.
        """

        if numpy_matrix is None:
            # Check that the second dimension matches the length of the default list
            if len(default_labels) != 1:
                if dimensions[1] > len(default_labels):
                    raise ValueError("The second dimension must match the length of the default values list.")
            # Create the numpy array with the specified dimensions and default values
            flat_array = np.tile(default_labels, int(np.prod(dimensions) / len(default_labels)))
            obj = flat_array.reshape(dimensions).view(cls)
        else:
            if numpy_matrix.shape != tuple(dimensions):
                raise ValueError("numpy_matrix has to have the same shape as specified in the dimensions input.")
            else:
                obj = numpy_matrix.view(cls)
        

        # Set the id and available labels attribute to the object
        obj.available_labels = available_labels
        obj.dimensions_descriptions = dimensions_descriptions
        obj.actions_enabled = enable_actions     

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.available_labels = getattr(obj, 'available_labels', None)
        self.dimensions_descriptions = getattr(obj, 'dimensions_descriptions', None)
        self.actions_enabled = getattr(obj, 'actions_enabled', None)

    def __deepcopy__(self, memo):
        # Copy the underlying numpy array
        matrix = np.copy(self)

        available_labels = getattr(self, 'available_labels', None)
        dimensions_descriptions = getattr(self, 'dimensions_descriptions', None)
        actions_enabled = getattr(self, 'actions_enabled', None)

        # Create a new instance with the copied data and custom attributes
        new_obj = ActionSpace(list(self.shape),
                            None, # We are using the numpy_matrix argument, the body of the array will not nead to be initialized
                            copy.deepcopy(available_labels, memo),
                            copy.deepcopy(dimensions_descriptions, memo),
                            numpy_matrix=matrix,
                            enable_actions=copy.deepcopy(actions_enabled, memo))
        # Add the new object to the memo dictionary to handle recursive copying
        memo[id(self)] = new_obj
        return new_obj