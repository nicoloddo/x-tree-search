from abc import ABC, abstractmethod

import asyncio

class GameAgent(ABC):
    def __init__(self, *, agent_id):
        self.id = agent_id
    
    @abstractmethod
    async def play(self, game, inputs=None):
        pass

class AIAgent(GameAgent):
    def __init__(self, *, agent_id, core):
        """
        GameAgent initialization.

        :param core: The core of the agent.
        :type core: object
        :param agent_id: The ID of the agent.
        :type agent_id: str
        :raises SyntaxError: If the core does not have a 'last_choice' attribute or a 'nodes' attribute.
        """
        super().__init__(agent_id=agent_id)
        self.core = core
        if not hasattr(self.core, "last_choice"):
            raise SyntaxError("The core of a GameAgent must have a 'last_choice' attribute reflecting the last choice of the agent.")
        if not hasattr(self.core, "nodes"):
            raise SyntaxError("The core of a GameAgent must have a 'nodes' attribute reflecting the nodes of the agent.")

    async def play(self, game, inputs=None):
        #await asyncio.sleep(0.1)
        if game.gm.ended:
            return
    
        # Use the search algorithm to determine the best move        
        tree = game.tree

        current_state = tree.get_current_state()
        self_constraints = game.expansion_constraints_self(self.id)
        other_constraints = game.expansion_constraints_other(self.id)
        best_outcome, _ = self.core.run(current_state, expansion_constraints_self=self_constraints, expansion_constraints_other=other_constraints)
        
        if best_outcome is None:
            return
        
        action = best_outcome.action
        
        # Apply the move to the game
        if action is not None:
            await asyncio.to_thread(game.act, action)
    
    @property
    def choice(self):
        return self.core.last_choice
    
class AIAgentOpSp(GameAgent):
    def __init__(self, *, agent_id, core):
        super().__init__(agent_id=agent_id)
        self.core = core

    async def play(self, game, inputs=None):
        #await asyncio.sleep(0.1)
        if game.ended:
            return
        
        _, action = self.core.run(game.model, game.state, self.id)
        game.act(opsp_action=action, player=self.id)

    @property
    def choice(self):
        return self.core.last_choice


class User(GameAgent):
    def __init__(self, *, agent_id, ask_what=True, ask_where=True, pause_first_turn=False):
        super().__init__(agent_id=agent_id)
        self.ask_what = ask_what
        self.ask_where = ask_where
        self.pause_first_turn = pause_first_turn

    async def play(self, game, inputs=None):
        if game.interface_mode == 'jupyter' or game.interface_mode == 'gradio':
            what = inputs['what']
            where = inputs['where']
            action_space = inputs['on']
            action = {'who': self.id, 'where': where, 'what': what, 'on': action_space}
            game.act(action)
            if game.interface_mode == 'jupyter': # For gradio this should be handled by the interface
                game.interface.update()  # Update after user's move
                await game.continue_game()
                game.interface.update()  # Update again after AI's move

        if game.interface_mode == 'cmd':
            
            if self.pause_first_turn:
                game.stop = True
                return

            await asyncio.sleep(1)
            if game.gm.ended:
                return
        
            who = self.id

            if self.ask_what:
                what = await self.async_input(game.what_question)

                if what == 'exit':
                    game.stop = True
                    return
                elif what == '':
                    await asyncio.sleep(0.5)
                else:
                    try:
                        what = game.parse_what_input(what)
                    except ValueError:
                        print("Invalid input format. Please use the correct format for the action.")
                        return await self.async_input(game.what_question)
            else:
                what = ''
            
            if self.ask_where:
                where_str = await self.async_input(game.where_question)
                
                if where_str == 'exit':
                    game.stop = True
                    return
                elif where_str == '':
                    await asyncio.sleep(0.5)
                    return await self.async_input(game.where_question)
                else:
                    try:
                        where = game.parse_where_input(where_str)
                    except ValueError:
                        print("Invalid input format. Please use 'x,y' format.")
                        return await self.async_input(game.where_question)
            else:
                where = ''
            
            action = {'who': who, 'where': where, 'what': what}
            await asyncio.to_thread(game.act, action)

    async def async_input(self, prompt: str) -> str:
        # Ensure proper input handling in Jupyter
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)