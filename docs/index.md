# Introduction

The x-tree-search library provides a flexible system for defining propositions and inferences about nodes in a tree-based structure. Given the framework you can then explain any decision made by the algorithm in an interactive argumentative way.

# Usage

To explain the usage of the library, it is best to refer to a concrete example.

Suppose to have a MiniMax algorithm.<br>
The algorithm gives scores to the leaf nodes based on a scoring function. For non-leaf nodes, it backpropagates the score of the best or worst child, depending on if the maximizing or minimizing player is playing.<br>
The nodes of the tree built by the algorithm can be seen as moves in the game, where the score is the outcome of the game from the perspective of the main (maximizing) player.<br>
If the main player is playing, the move will be the best move available, while if the opponent is playing, their move will be the worst move available from our perspective.

When the algorithm takes a decision, it inherently finds a node/move which could be described as the "best".
To argumentatively explain the decision made by our minimax, we therefore have to define where do the adjectives "best" and "worst" come from for a node.<br>
Thus:
1. We declare a quantitative "score" adjective, defined by the node.score parameter.
```python
QuantitativePointerAdjective("score",
    definition = "node.score")
```
2. With this quantitative adjective, we can then define what means for a node to be better or worse with a comparison adjective.
```python
ComparisonAdjective("better", "score", ">")
```
3. With a comparison adjective, we can define the "best" and "worst" adjectives.    
```python
MaxRankAdjective("best", "better", "siblings")
MinRankAdjective("worst", "better", "siblings")
```
4. Note that for a node to be defined as "best" or "worst", it must be the best or worst score among a group of nodes, which in this case is defined by the "siblings" adjective.
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

While comparison adjectives and rank adjectives can usually be inherently explained by their definition, pointer adjectives often need an explanation of their own.<br>
By default, adjectives in the framework are explained by their definition. But we can provide a more detailed explanation mechanism by utilizing the explanation parameter in any adjective's constructor:
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
We have thus specified a mechanism to explain the score of a node by referring to other adjectives.<br>
In this case, the explanation is conditional on the node being a leaf or not:
- If the node is a leaf, we explain the score with an assumption: the score simply comes from the evaluation function.
- If the node is not a leaf, the score comes from a selected child, we thus refer to the backpropagating child's possession of the score.

The Possession explanation refers to the node's possession of the backpropagating child adjective, and the backpropagating child's possession of the score adjective. Both these adjectives will need to be explained further, and so on until we reach an assumption, or a recursion limit.

All explanations need to refer to other adjectives except assumptions, which are the base of the explanation hierarchy.

Notice that the backpropagating child adjective has to be defined for this explanation to work, but the order of definition of the adjectives does not matter.
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
Check the documentation of [Explanations](rst/explanation) for more details on how to create explanations.

When giving an explanation, think of explanation classes as providing a statement like "because the node possesses this backpropagating child, and this backpropagating child is the best option (possesses the adjective "best")"

Adjectives must be added to an ArgumentationFramework, which will be attached to an ArgumentativeExplainer, that can then be used to explain a decision. ArgumentativeExplaners support multiple frameworks, which can be switched at runtime. The first framework attached to the explainer will be used as default. Different frameworks can be useful if we want to explain the same decision to different types of users, with different levels of expertise: one could be to explain a decision to a game playing user, another for debugging purposes for the search tree developer.

The definition of the adjectives must be a valid python expression, using the node object to refer to the current node being explained.

To declare an explainer and a framework, we can use the following code:
```python
# Create explainer
explainer = ArgumentativeExplainer()
# Create argumentation framework
highlevel_framework = ArgumentationFramework(
    refer_to_nodes_as='move',
    adjectives=adjectives,
    tactics=tactics,
    settings=settings,
)
# Add framework to explainer
explainer.add_framework("highlevel", highlevel_framework)
```
The adjectives must be a list of instances declared like in the examples above.<br>
The tactics must be a list of instances of ArgumentationTactic.<br>
The settings must be a dictionary containing the settings for the framework.<br>

```python
# Define settings
settings = {
    'explanation_depth': 4,
    'print_implicit_assumptions': False,
    'assumptions_verbosity': 'verbose',
    'print_mode': 'verbal',
}
```
You can check the respective documentations of the [Adjectives](rst/adjective), [Tactics](rst/tactic) and [Settings](rst/setting) for more details.


# Modules
```{toctree}
:maxdepth: 2
:caption: Contents:

rst/adjective
rst/explanation
```