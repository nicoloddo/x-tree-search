# x-tree-search Library Documentation

> **Disclaimer:** This documentation is currently under construction. Please check back later for more comprehensive information and updates.

## Table of Contents
- [Introduction](#introduction)
- [Usage](#usage)
  - [Example: MiniMax Algorithm](#example-minimax-algorithm)
  - [Defining Adjectives](#defining-adjectives)
  - [Explaining Adjectives](#explaining-adjectives)
  - [Creating an Explainer and Framework](#creating-an-explainer-and-framework)
- [Modules](#modules)

## Introduction

The x-tree-search library provides a flexible system for defining propositions and inferences about nodes in a tree-based structure. Given the framework, you can then explain any decision made by the algorithm in an interactive argumentative way.

## Usage

To illustrate the usage of the library, let's refer to a concrete example.

### Example: MiniMax Algorithm

Consider a MiniMax algorithm with the following characteristics:
- Scores leaf nodes based on a scoring function
- Backpropagates scores for non-leaf nodes
- Nodes represent moves in the game
- Scores reflect the game outcome from the main (maximizing) player's perspective
- Main player chooses the best move, opponent chooses the worst move (from main player's perspective)

### Defining Adjectives

To argumentatively explain decisions, we need to define adjectives like "best" and "worst" for nodes:

1. Define a quantitative "score" adjective:
   ```python
   QuantitativePointerAdjective("score",
       definition = "node.score")
   ```

2. Define a comparison adjective for "better":
   ```python
   ComparisonAdjective("better", "score", ">")
   ```

3. Define "best" and "worst" adjectives:
   ```python
   MaxRankAdjective("best", "better", "siblings")
   MinRankAdjective("worst", "better", "siblings")
   ```

4. Define the "siblings" adjective among which the "best" and "worst" adjectives are evaluated:
   ```python
   PointerAdjective("siblings",
       definition = "[sibling for sibling in node.parent.children if sibling is not node]")
   ```

With these adjectives, the explainer will be able to reply to the query "Why is this node/move "best"?" with the following argument:<br>
> The node has these siblings: [list of siblings]<br>
> The node is better than sibling1 because node's score > sibling1's score<br>
> The node is better than sibling2 because node's score > sibling2's score<br>
> ...<br>
> Therefore the node is better than all its siblings.<br>
> Since "best" is the best node among its siblings, the node is best.<br>

The above explanation, though, does not explain why the node has the score it has, nor why it has the children it has.

While comparison adjectives (e.g. "better") and rank adjectives (e.g. "best") can usually be inherently explained by their definition, pointer adjectives (e.g. "score") often need more complex explanations: why does the node have this specific score?

### Explaining Adjectives

By default, adjectives in the framework are explained by their definition.<br>
To provide more detailed explanations, use the `explanation` parameter in adjective constructors:

```python
QuantitativePointerAdjective("score",
    definition = "node.score",
    explanation = ConditionalExplanation(
        condition = If("leaf"),
        explanation_if_true = Assumption("Leaf nodes have scores from the evaluation function"),
        explanation_if_false = CompositeExplanation(
            Assumption("Internal nodes have scores from children"),
            Possession("backpropagating child", "score")
        )
    )
)
```
Since we referred to an adjective "backpropagating child" in the explanation of "score", we need to define it:
```python
PointerAdjective("backpropagating child",
    definition = "node.score_child",
    explanation = ConditionalExplanation(
        condition = If("opponent player turn"),
        explanation_if_true = CompositeExplanation(
            Assumption("We assume the opponent will do their best move."),
            Possession("backpropagating child", "worst")),
        explanation_if_false = CompositeExplanation(
            Assumption("On our turn we take the maximum rated move."),
            Possession("backpropagating child", "best"))
    )
)
```
Explanations will continue to be created recursively, as they refer to other adjectives.<br>
Only assumptions stop the recursions since they don't refer to other adjectives.

For more details on creating explanations, refer to the [Explanations](rst/explanation) documentation.

### Creating an Explainer and Framework

To set up an explainer and framework:

```python
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
highlevel_framework = ArgumentationFramework(
    refer_to_nodes_as='move',
    adjectives=adjectives, # List of adjective instances as defined above
    tactics=tactics,
    settings=settings,
)

# Add framework to explainer
explainer.add_framework("highlevel", highlevel_framework)
```
For a more structured example, check the [Alphabeta Explainer](explainers/alphabeta_explainer.py) example.<br>
For more information, check the documentation for [Adjectives](rst/adjective), [Tactics](rst/tactic), and [Settings](rst/setting).

## Modules

```{toctree}
:maxdepth: 2
:caption: Contents:

rst/explainer
rst/framework
rst/settings
rst/adjective
rst/explanation
rst/tactic
```