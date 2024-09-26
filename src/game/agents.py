import asyncio

class GameAgent:
    def __init__(self, *, core, agent_id):
        self.core = core
        self.id = agent_id

    async def play(self, game):
        await asyncio.sleep(0.1)
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

class User:
    def __init__(self, *, agent_id, ask_what=True, ask_where=True, pause_first_turn=False):
        self.id = agent_id
        self.ask_what = ask_what
        self.ask_where = ask_where
        self.pause_first_turn = pause_first_turn

    async def play(self, game, inputs=None):
        if game.interface_mode == 'jupyter' or game.interface_mode == 'gradio':
            what = inputs['what']
            where = inputs['where']
            action_space = inputs['action_space']
            action = {'who': self.id, 'where': where, 'what': what, 'action_space': action_space}
            game.act(action)
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
                what = await self.async_input("Insert what [insert 'exit' to exit] [click enter with no input to refresh]: ")

                if what == 'exit':
                    game.stop = True
                    return
                if what == '':
                    await asyncio.sleep(0.5)
            else:
                what = ''
            
            if self.ask_where:
                where_input_question = "Insert where (format: x,y) [insert 'exit' to exit] [click enter with no input to refresh]: "
                where_str = await self.async_input(where_input_question)
                
                if where_str == 'exit':
                    game.stop = True
                    return
                elif where_str == '':
                    await asyncio.sleep(0.5)
                    return await self.async_input(where_input_question)
                else:
                    try:
                        x, y = map(int, where_str.split(','))
                        where = (x, y)
                    except ValueError:
                        print("Invalid input format. Please use 'x,y' format.")
                        return await self.async_input(where_input_question)
            else:
                where = ''
            
            action = {'who': who, 'where': where, 'what': what}
            await asyncio.to_thread(game.act, action)

    async def async_input(self, prompt: str) -> str:
        # Ensure proper input handling in Jupyter
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)