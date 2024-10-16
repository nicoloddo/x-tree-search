from games.tic_tac_toe import TicTacToe, simple_depth_dependant_scoring_function
from src.game.agents import GameAgent, User
from algorithms.minimax import MiniMax
from games.tic_tac_toe.interface import TicTacToeGradioInterface
from explainers.alphabeta_explainer import AlphaBetaExplainer
import asyncio

def create_game_method():
    opponent = GameAgent(agent_id=0, core=MiniMax(simple_depth_dependant_scoring_function, max_depth=6, use_alpha_beta=True))
    game = TicTacToe(players=[opponent, User(agent_id=1)],
                    interface_mode='gradio', 
                    interface_hyperlink_mode=True)

    game.explaining_agent = opponent
    return game

explainer = AlphaBetaExplainer()
interface = TicTacToeGradioInterface(create_game_method=create_game_method, explainer=explainer)
interface.start()