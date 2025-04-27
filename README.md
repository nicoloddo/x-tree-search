---
title: X Tree Search
emoji: 👁️‍🗨️
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: cc-by-nc-4.0
short_description: Tree-Search algorithms interactive explainer
---

# x-tree-search Library

> **Note:** This library is currently under development. Documentation and features may be incomplete or subject to change.

## Introduction

The x-tree-search library provides a flexible system for defining propositions and inferences about nodes in a tree-based structure. It allows you to explain decisions made by tree-search algorithms in an interactive, argumentative way.

## Documentation

For more detailed information on how to use x-tree-search, including advanced features and full API documentation, please visit our [Read the Docs page](https://x-tree-search.readthedocs.io/en/latest/).

## Quick Start

Here's a brief, simplified example of how to use x-tree-search to explain a MiniMax algorithm:

1. Define adjectives for your nodes:

```python
from x_tree_search import QuantitativePointerAdjective, ComparisonAdjective, MaxRankAdjective, MinRankAdjective, PointerAdjective

adjectives = [
    # Define a "score" adjective
    QuantitativePointerAdjective("score", definition="node.score"),

    # Define a "better" comparison adjective
    ComparisonAdjective("better", "score", ">"),

    # Define "best" and "worst" adjectives
    MaxRankAdjective("best", "better", "siblings"),
    MinRankAdjective("worst", "better", "siblings"),

    # Define "siblings" adjective
    siblings = PointerAdjective("siblings",
        definition="[sibling for sibling in node.parent.children if sibling is not node]")
]
```

2. Create an explainer and framework:

```python
from x_tree_search import ArgumentativeExplainer, ArgumentationFramework

# Create explainer
explainer = ArgumentativeExplainer()

# Define settings
settings = {
    'explanation_depth': 4,
    'print_implicit_assumptions': False,
    'assumptions_verbosity': 'verbose',
    'print_mode': 'verbal',
}

# Create argumentation framework
framework = ArgumentationFramework(
    refer_to_nodes_as='move',
    adjectives=adjectives,
    tactics=[],  # Add your tactics here
    settings=settings,
)

# Add framework to explainer
explainer.add_framework("minimax", framework)
```

3. Use the explainer to explain decisions:

```python
# Assuming you have a node object from your MiniMax algorithm
explainer.explain(node, "best")
```

## Installation

### Basic Installation

To install the basic x-tree-search package:

1. Install the required dependencies:
On Windows, open the requirements.txt file and comment the lines indicated in the comment before doing this.

```bash
pip install -r requirements.txt
```

2. If you are on Windows, you commented out torch and open_spiel. Install PyTorch by following the official installation instructions at [pytorch.org](https://pytorch.org/). Choose the appropriate version for your operating system, package manager, and compute platform.

### Graphviz Installation

This library uses Graphviz for visualization of decision trees. You need to install both the Python package and the system-level Graphviz executable:

1. **Install the Python package** (already included in requirements.txt):
   ```bash
   pip install graphviz
   ```

2. **Install the system-level Graphviz executable**:

   - **Windows**:
     - Download and install from [Graphviz's official download page](https://graphviz.org/download/)
     - Add the Graphviz bin directory to your system PATH (typically `C:\Program Files\Graphviz\bin`)

   - **macOS**:
     ```bash
     brew install graphviz
     ```

   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install graphviz
     ```

   - **CentOS/RHEL**:
     ```bash
     sudo yum install graphviz
     ```

If you encounter errors like `ExecutableNotFound: failed to execute dot, make sure the Graphviz executables are on your systems' PATH`, ensure the Graphviz executables are properly installed and added to your PATH.

### OpenSpiel Integration

If you want to use the OpenSpiel wrapper:

1. Install OpenSpiel by following their installation guidance on [GitHub](https://github.com/google-deepmind/open_spiel)

2. Then install the specific OpenSpiel version required by x-tree-search (already in the requirements.txt for non windows users):

```bash
pip install open_spiel==1.5
```

## Contributing

We welcome contributions! Please contact me for more information at nicoloddo.r@gmail.com

## License

This project is licensed under the Creative Commons Attribution Non-Commercial 4.0 International License (CC BY-NC 4.0).

This means you are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- Attribution 
- NonCommercial

You can find more information about the license [here](https://creativecommons.org/licenses/by-nc/4.0/).
