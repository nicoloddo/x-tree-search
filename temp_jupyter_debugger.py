# %%
from src.tree import Tree

# %%
t = Tree()
print(t)

# %%
t.set_children('0', 4)
print(t)

# %%
t.nodes

# %%
t.get_node('01')