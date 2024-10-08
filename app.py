from games.tic_tac_toe import TicTacToe, simple_depth_dependant_scoring_function
from src.game.agents import GameAgent, User
from algorithms.minimax import MiniMax
from explainers.alphabeta_explainer import AlphaBetaExplainer
import gradio as gr
import asyncio

def create_and_start_game():
    explainer = AlphaBetaExplainer()
    opponent = GameAgent(agent_id=0, core=MiniMax(simple_depth_dependant_scoring_function, max_depth=6, use_alpha_beta=True))
    game = TicTacToe(players=[opponent, User(agent_id=1)], 
                     explainer=explainer, 
                     interface_mode='gradio', 
                     interface_hyperlink_mode=True)
    
    # Run start_game asynchronously and get the interface
    interface = asyncio.run(game.start_game())
    return interface

if __name__ == "__main__":
    iface = gr.Interface(fn=create_and_start_game, inputs=None, outputs="html")
    iface.launch()