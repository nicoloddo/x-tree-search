from games.tic_tac_toe import TicTacToe, simple_depth_dependant_scoring_function
from src.game.agents import GameAgent, User
from algorithms.minimax import MiniMax
from explainers.alphabeta_explainer import AlphaBetaExplainer
import asyncio

explainer = AlphaBetaExplainer()
opponent = GameAgent(agent_id=0, core=MiniMax(simple_depth_dependant_scoring_function, max_depth=6, use_alpha_beta=True))
game = TicTacToe(players=[opponent, User(agent_id=1)], 
                 explainer=explainer, 
                 interface_mode='gradio', 
                 interface_hyperlink_mode=True)

asyncio.run(game.start_game())