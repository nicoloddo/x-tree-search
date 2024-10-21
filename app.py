from games.tic_tac_toe import TicTacToe, simple_depth_dependant_scoring_function
from src.game.agents import AIAgent, User
from algorithms.minimax import MiniMax
from games.tic_tac_toe.interface.gradio_interface import TicTacToeGradioInterface
from explainers.alphabeta_explainer import AlphaBetaExplainer

opponent = AIAgent(agent_id=0, core=MiniMax(simple_depth_dependant_scoring_function, max_depth=6, use_alpha_beta=True))
game = TicTacToe(players=[opponent, User(agent_id=1)],
                interface_mode='gradio', 
                interface_hyperlink_mode=True)
game.explaining_agent = opponent

explainer = AlphaBetaExplainer()

# game and explainer are utilized as States in the interface,
# thus they are not shared across users.
interface = TicTacToeGradioInterface(game, explainer, interface_hyperlink_mode=True)
interface.start()