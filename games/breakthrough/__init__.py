from .breakthrough import Breakthrough
try:
    from .breakthrough_opsp import BreakthroughOpSp
except ImportError:
    pass

from .scoring import simple_depth_dependant_scoring_function