import asyncio
import os
import numpy as np
import copy

from src.game.interface.interface import GameInterface

class GameCmdInterface(GameInterface):
    def __init__(self, game):
        super().__init__(game)

    def start(self):
        asyncio.run(self._start_game())
        
    def clear_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console

    def update_display(self, current_state):
        """Override in the specific game if you want to change its way of display"""
        self.clear_console()
        print(current_state)

    async def _start_game(self):
        # Start the state monitoring task
        self.game.stop = False
        state_monitoring_task = asyncio.create_task(self._monitor_game_state())

        self.output(self.game.tree.get_current_state().state)

        while not self.game.model.ended and not self.game.stop:
            await asyncio.gather(*(player.play(self.game) for player in self.game.players.values()))
            await asyncio.sleep(0.1)  # Reduced sleep time for more responsive updates

        # Stop the state monitoring task
        state_monitoring_task.cancel()

        self.update()
        self.output("")
        if self.game.stop:
            self.output("Game paused.")
        elif self.game.model.ended:
            self.output("Game finished.")
        self.output("")
        self.output(self.game.tree.get_current_state().state)

    async def _monitor_game_state(self):
        """Periodically checks the game's current state and prints it if it has changed."""
        while not self.game.model.ended and not self.game.stop:
            current_state = self.game.tree.get_current_state().state

            if not np.array_equal(current_state, self._previous_state):
                self.update_display(current_state)
                self._previous_state = copy.deepcopy(current_state)
            
            await asyncio.sleep(0.2)  # Adjust the sleep time as needed

    def output(self, text: str) -> None:
        print(text)

    def update(self):
        current_state = self.game.tree.get_current_state().state
        self.update_display(current_state)
        self._previous_state = copy.deepcopy(current_state)
