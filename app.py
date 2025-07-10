from src.game.agents import AIAgent, AIAgentOpSp, User
from explainers.alphabeta_explainer import AlphaBetaExplainer
from explainers.minimax_explainer import MiniMaxExplainer

"""
PARAMETERS

game: The game to play.
use_alpha_beta: Whether to use AlphaBetaExplainer or MiniMaxExplainer.
players_order: The order of the players. (Not possible to set for OpenSpiel games)
"""
game = "tic_tac_toe"
use_alpha_beta = False
players_order = ["human", "AI"]
"""
END OF PARAMETERS
"""

if game == "tic_tac_toe":
    from games.tic_tac_toe import TicTacToe as Game
    from games.tic_tac_toe.interface.gradio_interface import (
        TicTacToeGradioInterface as Interface,
    )
    from algorithms.minimax import MiniMax
    from games.tic_tac_toe import (
        simple_depth_dependant_scoring_function as ai_scoring_function,
    )

    max_depth = 6

elif game == "tic_tac_toe_opsp":
    try:
        from games.tic_tac_toe import TicTacToeOpSp as Game
        from games.tic_tac_toe.interface.gradio_interface import (
            TicTacToeGradioInterface as Interface,
        )
        from algorithms.minimax_openspiel_wrapper import MiniMax
        from games.tic_tac_toe import (
            simple_depth_dependant_scoring_function as ai_scoring_function,
        )

        AIAgent = AIAgentOpSp
        max_depth = 6
    except ImportError:
        raise ImportError(
            "OpenSpiel is not installed. Please install it using the instructions in the README."
        )

elif game == "breakthrough":
    from games.breakthrough import Breakthrough as Game
    from games.breakthrough.interface.gradio_interface import (
        BreakthroughGradioInterface as Interface,
    )
    from algorithms.minimax import MiniMax
    from games.breakthrough import (
        simple_depth_dependant_scoring_function as ai_scoring_function,
    )

    max_depth = 4

elif game == "breakthrough_opsp":
    try:
        from games.breakthrough import BreakthroughOpSp as Game
        from games.breakthrough.interface.gradio_interface import (
            BreakthroughGradioInterface as Interface,
        )
        from algorithms.minimax_openspiel_wrapper import MiniMax
        from games.breakthrough import (
            simple_depth_dependant_scoring_function_opsp as ai_scoring_function,
        )

        AIAgent = AIAgentOpSp
        max_depth = 6
        players_order = [
            "AI",
            "human",
        ]  # For some reason in OpenSpiel's Breakthrough the blacks go first
    except ImportError:
        raise ImportError(
            "OpenSpiel is not installed. Please install it using the instructions in the README."
        )

else:
    raise ValueError("The selected game is not available.")

ids = {
    "human": next(i for i, p in enumerate(players_order) if p == "human"),
    "AI": next(i for i, p in enumerate(players_order) if p == "AI"),
}

opponent = AIAgent(
    agent_id=ids["AI"],
    core=MiniMax(
        ai_scoring_function, max_depth=max_depth, use_alpha_beta=use_alpha_beta
    ),
)

game = Game(
    players=[opponent, User(agent_id=ids["human"])],
    interface_mode="gradio",
    interface_hyperlink_mode=True,
)
game.explaining_agent = opponent

title = game.__class__.__name__ + " vs MiniMax"
title += "\nChoose the search depth or enable AlphaBeta pruning in the settings tab."

if use_alpha_beta:
    explainer = AlphaBetaExplainer()
else:
    explainer = MiniMaxExplainer()

# game and explainer are utilized as States in the interface,
# thus they are not shared across users.
interface = Interface(
    game,
    explainer,
    interface_hyperlink_mode=True,
    game_title_md=f"# {title}",
)
interface.start()
