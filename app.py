from games.tic_tac_toe import TicTacToe, simple_depth_dependant_scoring_function as tic_tac_toe_scoring_function
from games.breakthrough import Breakthrough, simple_depth_dependant_scoring_function as breakthrough_scoring_function
from src.game.agents import AIAgent, User
from algorithms.minimax import MiniMax
from games.tic_tac_toe.interface.gradio_interface import TicTacToeGradioInterface
from games.breakthrough.interface.gradio_interface import BreakthroughGradioInterface
from explainers.alphabeta_explainer import AlphaBetaExplainer

game = 'breakthrough'

if game == 'tic_tac_toe':
    ai_scoring_function = tic_tac_toe_scoring_function
    max_depth = 6
    game_class = TicTacToe
    interface_class = TicTacToeGradioInterface
elif game == 'breakthrough':
    ai_scoring_function = breakthrough_scoring_function
    max_depth = 1
    game_class = Breakthrough
    interface_class = BreakthroughGradioInterface

use_ai_opponent = False

opponent = AIAgent(agent_id=0, core=MiniMax(ai_scoring_function, max_depth=max_depth, use_alpha_beta=True))

game = game_class(players=[opponent, User(agent_id=1)],
                interface_mode='gradio', 
                interface_hyperlink_mode=True)
game.explaining_agent = opponent

explainer = AlphaBetaExplainer()

# game and explainer are utilized as States in the interface,
# thus they are not shared across users.
interface = interface_class(game, explainer, interface_hyperlink_mode=True)
interface.start()