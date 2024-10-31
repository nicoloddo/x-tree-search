from .tic_tac_toe import TicTacToe
try:
    from .tic_tac_toe_opsp import TicTacToeOpSp
except ImportError:
    pass
from .scoring import simple_scoring_function, simple_depth_dependant_scoring_function