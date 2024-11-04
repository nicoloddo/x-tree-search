from src.game.agents import AIAgent, AIAgentOpSp, User
from explainers.alphabeta_explainer import AlphaBetaExplainer

game = 'breakthrough_opsp'

players_order = ['human', 'AI']

if game == 'tic_tac_toe':
    from games.tic_tac_toe import TicTacToe as Game
    from games.tic_tac_toe.interface.gradio_interface import TicTacToeGradioInterface as Interface
    from algorithms.minimax import MiniMax
    from games.tic_tac_toe import simple_depth_dependant_scoring_function as ai_scoring_function
    max_depth = 6

elif game == 'tic_tac_toe_opsp':
    from games.tic_tac_toe import TicTacToeOpSp as Game
    from games.tic_tac_toe.interface.gradio_interface import TicTacToeGradioInterface as Interface
    from algorithms.minimax_openspiel_wrapper import MiniMax
    from games.tic_tac_toe import simple_depth_dependant_scoring_function as ai_scoring_function
    AIAgent = AIAgentOpSp
    max_depth = 6

elif game == 'breakthrough':
    from games.breakthrough import Breakthrough as Game
    from games.breakthrough.interface.gradio_interface import BreakthroughGradioInterface as Interface
    from algorithms.minimax import MiniMax
    from games.breakthrough import simple_depth_dependant_scoring_function as ai_scoring_function
    max_depth = 4

elif game == 'breakthrough_opsp':
    from games.breakthrough import BreakthroughOpSp as Game
    from games.breakthrough.interface.gradio_interface import BreakthroughGradioInterface as Interface
    from algorithms.minimax_openspiel_wrapper import MiniMax
    from games.breakthrough import simple_depth_dependant_scoring_function_opsp as ai_scoring_function
    AIAgent = AIAgentOpSp
    max_depth = 6
    players_order = ['AI', 'human'] # For some reason in OpenSpiel's Breakthrough the blacks go first
    
else:
    raise ValueError("The selected game is not available.")

ids = {
    'human': next(i for i, p in enumerate(players_order) if p == 'human'),
    'AI': next(i for i, p in enumerate(players_order) if p == 'AI')
}

opponent = AIAgent(agent_id=ids['AI'], core=MiniMax(ai_scoring_function, max_depth=max_depth))

game = Game(players=[opponent, User(agent_id=ids['human'])],
                interface_mode='gradio', 
                interface_hyperlink_mode=True)
game.explaining_agent = opponent

explainer = AlphaBetaExplainer()

# game and explainer are utilized as States in the interface,
# thus they are not shared across users.
interface = Interface(game, explainer, interface_hyperlink_mode=True)
interface.start()