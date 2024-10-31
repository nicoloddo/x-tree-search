from games.tic_tac_toe import simple_depth_dependant_scoring_function as tic_tac_toe_scoring_function
from games.breakthrough import simple_depth_dependant_scoring_function as breakthrough_scoring_function

from src.game.agents import AIAgent, AIAgentOpSp, User
from games.tic_tac_toe.interface.gradio_interface import TicTacToeGradioInterface
from games.breakthrough.interface.gradio_interface import BreakthroughGradioInterface
from explainers.alphabeta_explainer import AlphaBetaExplainer

game = 'breakthrough'

if game == 'tic_tac_toe':
    from games.tic_tac_toe import TicTacToe
    from algorithms.minimax import MiniMax
    ai_scoring_function = tic_tac_toe_scoring_function
    max_depth = 6
    game_class = TicTacToe
    interface_class = TicTacToeGradioInterface
elif game == 'tic_tac_toe_opsp':
    from games.tic_tac_toe import TicTacToeOpSp
    from algorithms.minimax_openspiel_wrapper import MiniMax, TreeNode
    TreeNode.game_state_translator = lambda cls, opsp_state: TicTacToeOpSp.game_state_translator(opsp_state)
    AIAgent = AIAgentOpSp
    ai_scoring_function = tic_tac_toe_scoring_function
    max_depth = 6
    game_class = TicTacToeOpSp
    interface_class = TicTacToeGradioInterface
elif game == 'breakthrough':
    from games.breakthrough import Breakthrough
    from algorithms.minimax import MiniMax
    ai_scoring_function = breakthrough_scoring_function
    max_depth = 4
    game_class = Breakthrough
    interface_class = BreakthroughGradioInterface

use_ai_opponent = False

opponent = AIAgent(agent_id=1, core=MiniMax(ai_scoring_function, max_depth=max_depth))

game = game_class(players=[opponent, User(agent_id=0)],
                interface_mode='gradio', 
                interface_hyperlink_mode=True)
game.explaining_agent = opponent

explainer = AlphaBetaExplainer()

# game and explainer are utilized as States in the interface,
# thus they are not shared across users.
interface = interface_class(game, explainer, interface_hyperlink_mode=True)
interface.start()