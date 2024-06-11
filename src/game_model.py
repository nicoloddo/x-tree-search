MAX_ENVIRONMENT_SIZE_TO_PRINT = 30

from common.utils import join_arrays_respective_elements

import numpy as np
import inspect

class GameModel:
    def __init__(self, default_labels, additional_labels, environment_dimensions, default_agents_labels, additional_agents_labels, agents_dimensions, dimensions_descriptions="No description was given.", game_name=""):
        """
        Initializes the GameModel with a labeled environment.

        Args:
            default_label (list of str): The default labels to assign to each column in the environment.
            additional_labels (list of str): Other possible labels that can be assigned to the environment elements.

            default_agents_labels (list of str)): The default labels to each row of agent features.
            additional_agents_labels (list of list of strings): For each agent feature, specify other possible labels that can be assigned to each.

            environment_dimensions (list of int): Dimensions of the environment matrix. 
            Consider adding an additional dimension to the environment for time if rules refer to previous timesteps.

            agents_dimensions (list of int): Dimensions of the agents matrix.
            Consider to use the first dimension for the number of player and the second dimension for the number of features.

            dimensions_descriptions (str): String explaining each dimension of the environment and of the agents (optional)
            game_name (str): String with the name of the game (optional)

        Attributes:
            game_name (str): String with the name of the game (optional)
            labels (list of str): A list containing all possible labels for environment positions.
            agents_labels (list of list): A list of list containing all possible labels for agents features.
            environment (numpy.ndarray): A matrix representing the environment, initialized with the default label.
            agents (numpy.ndarray): A matrix representing the agents and their features, initialized with the default labels.
            rules (list): A list of rules, where each rule is a function that takes (who, where, what, env) and returns a bool.
        """
        self.game_name = game_name

        # Combine the default label and additional labels into a single list
        self.labels = default_labels + additional_labels

        try:
            self.agents_labels = join_arrays_respective_elements(default_agents_labels, additional_agents_labels)
        except ValueError:
            raise ValueError("You should specify an alternative label for each default label.")
        
        # Initialize the environment matrix with the default labels
        self.environment = GameMatrix(environment_dimensions, default_labels)

        # Initialize the agents matrix with the default labels
        self.agents = GameMatrix(agents_dimensions, default_agents_labels)

        # Save the description
        self.dimensions_descriptions = dimensions_descriptions

        self.rules = {} # A dictionary of rules divided by action_space ids.

        self.actions = []

        self.timeline = []

        self.started = False # Boolean that keeps track of if the game has started (actions > 0)
        self.ended = False # Boolean that keeps track of if the game has ended

        self.endgame_dynamics = lambda: False # This function is checked after every action, if it returns True, the self.ended is changed to True
        self.action_is_violation_if(lambda who, where, what, which_agent_feature, game: game.ended, rule_description="Nothing is allowed if the game is ended.")

        print(f"""
        You can use the method gm.action_is_violation_if(rule, rule_description) to express rules for the game.\n
        Use help(gm.action_is_violation_if) for help on how to define rules.
        The rule: "Nothing is allowed if the game is ended." is defined by default, to delete it use gm.delete_rule(1).
        Use gm.print_rules() to see all the rules that have been setted.
        
        Use gm.set_endgame(callable_function(game)) to define based on what dynamics your game should end.
        The callable function should have one only input parameter, which represents the game itself, 
        which can be used to refer to anything inside its model, this include:
                - environment = the environment or board (e.g. game.environment)
                - agents = the agents involved in the game
                - actions = previous actions performed
                - started = if the game has started
                - ended = if the game has ended
        Example: 
            def three_elements_in_row(game):
                board = game.environment
                # Check rows for winning condition
                for row in board:
                    if row[0] == row[1] == row[2] != 'free':
                        return True
                # If no winner, return False
                return False
        \n""")

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
                board = game.environment
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

    ''' Rules definition'''
    def action_is_violation_if(self, rule, action_space = None, *, rule_description): # Any argument assigned to parameters after the asterisk * can only be passed as keyword (named) arguments.
        """
        Adds a new rule to the game model after validating the rule's signature and a test run to ensure it returns a boolean.

        Args:
            rule (callable): a previously defined function that returns True if your rule is violated.
            action_space: the action space to constrain with the rule. It refers to the matrix onto which the action is being performed, for example actions that modify the environment or the agents matrixes. 
                          If the action is more general, leave it empty and it will be applied to all action spaces.
            rule_description (str): a description for the rule.

        Definition of the rule:            
        - The rule has to have as input parameters exactly these 4: who, where, what, game
        - The rule has to return a bool which is True if the rule is violated. You can use a conditional as rule body.
        - The rule has to follow a specific formalism, with variable inside its body referring to:
            1. who = the agent making the action as index
            2. where = the position in the action space to apply the action to (as coordinates)
            3. what = the modification to apply (which should take the value of one of the declared labels and agents_labels)

            4. game = the GameModel, which can be used to refer to anything inside its model, this include:
                - environment = the environment or board
                - agents = the agents involved in the game
                - actions = previous actions performed
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
            mgm.action_is_violation_if(lambda who, where, what, game: where != 'free', mgm.environment, rule_description="The space needs to be free to put a sign on it.")
        
        
        3.  Rule: Agents cannot modify their features or the ones of other agents:

            Rule definition:
            mgm.action_is_violation_if(lambda who, where, what, game: where != [None], mgm.agents, rule_description="Agents cannot modify their own features.")
        """
        # Validate that the rule is a callable with the correct signature
        if not callable(rule):
            raise ValueError("The rule must be a callable function.")

        # Check the signature of the callable to ensure it has exactly four parameters
        sig = inspect.signature(rule)
        if len(sig.parameters) != 4:
            raise ValueError("Rule function must accept exactly these arguments: who, where, what, game")

        wrapped = lambda who, where, what: self.__wrapped_rule(rule, who, where, what, action_space)

        if action_space == None: # If no action_space has been specified, the rule is general and appliable to all scopes.
            for scope in rules:
                self.rules[scope].append({'description':rule_description, 'broken':wrapped})
        else:
            self.rules[action_space.id].append({'description':rule_description, 'broken':wrapped})
    
    def __wrapped_rule(self, rule, who, where, what, action_space):
        return rule(game.agents[who], action_space[tuple(where)], what, self)
    
    def __break_rules(self, who, where, what, action_space):
        """
        Checks all rules based on the given parameters.

        Args:
            who (int): Identifier for the entity performing the action as index of the respective row in the agents matrix
            where (list/tuple): Location or coordinates in the environment where the action takes place.
            what (str): The action or change being proposed.

        Returns:
            bool: Returns True if any rule is violated, otherwise False.
        """
        try:
            for i, rule in enumerate(self.rules[action_space.id]):
                try:
                    if rule['broken'](who, where, what):
                        print("Broke rule " + str(i+1) + ': ' + rule['description'])
                        return True
                except NoneIndexPassed: 
                    # Game matrixes will return a NoneIndexPassed exception when requested an element through a None index
                    # We pass a None as index of the matrix when its value is not important for the rule and the evaluation of that rule should be skipped
                        continue

        except Exception as e:
            # Log the error and possibly re-raise or handle it as necessary
            raise e
    
    def print_rules(self):
        print("Rules:")
        i = 1
        for rule in self.rules:
            print(str(i) + ': ' + rule['description'])
            i += 1

    def delete_rule(self, index):
        del self.rules[index - 1]


    ''' Actions dynamics'''
    def action(self, who, where, what, action_space):

    def action_on_environment(self, who, where, what):
        """
        Executes an action within the environment, modifying its state if the action does not break any rules.

        Args:
            who (int): Identifier for the entity performing the action as index of the respective row in the agents matrix
            where (list/tuple): Location or coordinates in the environment where the action takes place.
            what (str): The action or change being proposed.

        Returns:
            False if the action breaks any rules; otherwise, returns the action.
        """
        if self.__break_rules(who, where, what, [None]):
            print("This action is not permitted.\n")
            return False
        else:
            self.transform_env(where, what)
            self.__update_timeline()
            return self.__action_performed({'who':who, 'where':where, 'what':what, 'which_agent_feature':None, 'on':'environment'})

    def action_on_agent(self, who, what, which_agent_feature):
        """
        Executes an action within the environment, modifying its state if the action does not break any rules.

        Args:
            who (int): Identifier for the entity performing the action as index of the respective row in the agents matrix
            which_agent_feature (list/tuple): Location or coordinates in the agents matrix to the feature to modify.
            what (str): The action or change being proposed.

        Returns:
            False if the action breaks any rules; otherwise, returns the action.
        """
        if self.__break_rules(who, [None], what, which_agent_feature):
            print("This action is not permitted.")
            return False
        else:
            self.transform_agent(which_agent_feature, what)
            self.__update_timeline()
            return self.__action_performed({'who':who, 'where':None, 'what':what, 'which_agent_feature':which_agent_feature, 'on':'agent'})
            
    def __action_performed(self, action):
        self.actions.append(action)
        self.check_started()
        self.check_ended()
        return action

    def __update_timeline(self):
        self.timeline.append(self.environment)

    def transform_env(self, where, what):
        if what not in self.labels:
            raise ValueError("Transformations of the environment can only be done with the given labels.")
        self.environment[tuple(where)] = what

    def transform_agent(self, which_agent_feature, what):
        if not any(what in sublist for sublist in self.agents_labels): # if what is not in any sublist
            raise ValueError("Transformations of the agent features can only be done with the given labels.")
        self.agents[tuple(which_agent_feature)] = what

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

        to_return += f"Number of agents: {self.agents.shape[0]}, Number of agent features: {self.agents.shape[1]} \nAgent features labels: {self.agents_labels})\n\n"

        to_return += f"Environment shape: {self.environment.shape}, Total number of elements: {self.environment.size} \nLabels: {self.labels})\n\n"
        to_return += f"Dimensions Descriptions: {self.dimensions_descriptions}\n\n"

        to_return += f"Agents: \n{self.agents}\n"
        if self.environment.size < MAX_ENVIRONMENT_SIZE_TO_PRINT:
            to_return += f"\nEnvironment:\n{self.environment}"
        elif len(self.environment.shape) >= 2 and np.array(self.environment.shape[:2]).sum() < MAX_ENVIRONMENT_SIZE_TO_PRINT:
            # If the environment has at least two dimensions and their sum is not more than the max to print,
            # Create an index that selects the last element for all dimensions beyond the second
            index = [-1] * (self.environment.ndim - 2) + [slice(None), slice(None)]
            to_return += f"\nEnvironment:\n{self.environment[tuple(index)]}"
        else:
            to_return += f"\nEnvironment too big to print (greater than {MAX_ENVIRONMENT_SIZE_TO_PRINT} elements)"

        return to_return

class ActionSpace(np.ndarray):
    def __new__(cls, dimensions, default, action_space_id):
        """
        Create a numpy array with the given dimensions and default values for each row.
        
        Parameters:
        dimensions (list): List of integers indicating the shape of the numpy array.
        default (list): List of default values for each row.
        
        Returns:
        np.ndarray: Numpy array with the specified dimensions and default values.
        """
        # Check that the second dimension matches the length of the default list
        if len(default) != 1:
            if dimensions[1] > len(default):
                raise ValueError("The second dimension must match the length of the default values list.")

        # Create the numpy array with the specified dimensions and default values
        flat_array = np.tile(default, int(np.prod(dimensions) / len(default)))
        obj = flat_array.reshape(dimensions).view(cls)

        # Set the id attribute
        obj.id = action_extension_id

        return obj

    def __array_finalize__(self, obj):
        if obj is None: return  # Called during creation, ensure object exists
'''
    def __getitem__(self, index): # Wraps around the getitem of numpy.ndarray to check if a tuple([None]) index was passed.
        if index == tuple([None]):
            raise NoneIndexPassed("NoneType index means we should not check this matrix.")
        return super(GameMatrix, self).__getitem__(index)

class NoneIndexPassed(Exception):
    pass'''