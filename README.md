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

Installation guidance will be added soon.

## Contributing

We welcome contributions! Please contact me for more information at nicoloddo.r@gmail.com

## License

This project is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

This means you are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- Attribution — You must give appropriate credit citing the repository and authors.

You can find more information about the license [here](https://creativecommons.org/licenses/by/4.0/).
