class Tactic:
    """Abstract base class for all types of explanation tactics."""
    def __init__(self, name):
        self.name = name

    def apply(self):
        pass

class OnlyRelevantComparisons(Tactic):
    """When explaining a GroupComparison, only explain
    the comparison between relevant objects."""
    top_n = 'err'
    bottom_n = 'err'
    
    def __init__(self, *, mode: str):
        super().__init__(self.__class__.__name__)
        self.mode = mode

    def apply(self, group, value_for_comparison_adjective):
        if self.mode.startswith("top_"):
            characters_before_n = len("top_")
            n = self.mode[characters_before_n:]
            if n.isdigit() and int(n) > 0:
                self.top_n = int(n)
            else:
                raise ValueError("A top_n mode should have an integer greater than 0.")
            
            return self.relevant_top_n(group, value_for_comparison_adjective)
        
        if self.mode.startswith("bottom_"):
            characters_before_n = len("bottom_")
            n = self.mode[characters_before_n:]
            if n.isdigit() and int(n) > 0:
                self.bottom_n = n
            else:
                raise ValueError("A bottom_n mode should have an integer greater than 0.")
            
            return self.relevant_bottom_n(group, value_for_comparison_adjective)
        
    def relevant_top_n(self, group, value_for_comparison_adjective):
        return sorted(group, key=lambda obj: value_for_comparison_adjective.evaluate(obj), reverse=True)[:self.top_n]
    
    def relevant_bottom_n(self, group, value_for_comparison_adjective):
        return sorted(group, key=lambda obj: value_for_comparison_adjective.evaluate(obj), reverse=False)[:self.bottom_n]