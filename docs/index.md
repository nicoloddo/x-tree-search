# Introduction

The Argumentation Framework API provides a flexible system for defining propositions and inferences about nodes in a tree-based structure. Given the framework you can then explain any decision made by the algorithm in an interactive argumentative way.

# Usage Example: MinMax Tree Search

Here's an example of how to use the Argumentation Framework API to represent a minmax tree search reasoning.
Suppose to have a MinMax algorithm that gives scores to the leaf nodes and backpropagates the score of the best or worst child depending on if the maximizing or minimizing player is playing.

To argumentatively explain a decision made by our minmax, we have to define where do the adjectives "best" and "worst" come from for a node.
1. Thus, we declare a "score" adjective, linked to the node.score parameter.
2. Then we provide an explanation to why a node has a specific score.
3. This includes explaining what a leaf is,
4. And explaining how to choose the child from which the score has been backpropagated.
5. We then define what does it mean for a node to have a better score,
6. And finally define the "best" and "worst" adjectives.

```python
knowledgebase = ArgumentationFramework()

# Define "score" adjective
knowledgebase.add_adjective( 
    PointerAdjective("score",
        definition = "node.score",

        explanation = ConditionalExplanation(
            condition = If("leaf"),
            explanation_if_true = Assumption("Leaf nodes have scores from the evaluation function"),
            explanation_if_false = CompositeExplanation(
                Assumption("Internal nodes have scores from children"),
                Possession("backtracing child"))
        ))
)

# Define "leaf" adjective
knowledgebase.add_adjective( 
    BooleanAdjective("leaf",
        definition = "node.is_leaf")
)

# Define "opponent player turn" adjective
knowledgebase.add_adjective(
    BooleanAdjective("opponent player turn",
        definition = "not node.maximizing_player_turn")
)

# Define "backtracing child" adjective
knowledgebase.add_adjective( 
    PointerAdjective("backtracing child",
        definition = "node.score_child",
        explanation = ConditionalExplanation(
            condition = If("opponent player turn"),
            explanation_if_true = CompositeExplanation(
                Assumption("We assume the opponent will do their best move."),
                Possession("backtracing child", "worst")),
            explanation_if_false = CompositeExplanation(
                Assumption("On our turn we take the maximum rated move."),
                Possession("backtracing child", "best"))
        ))
)

# Define "better" comparison adjective
knowledgebase.add_adjective(
    ComparisonAdjective("better", "score", ">")
)

knowledgebase.add_adjective( 
    PointerAdjective("siblings",
        definition = "[sibling for sibling in node.parent.children if sibling is not node]")
)

knowledgebase.add_adjective(
    MaxRankAdjective("best", "better", "siblings")
)
knowledgebase.add_adjective(
    MinRankAdjective("worst", "better", "siblings")
)
```

# ArgumentationFramework

The main class that manages adjectives and their relationships.

```python
knowledgebase = ArgumentationFramework()
```

## Methods

### add_adjective(adjective: Adjective) -> None

Adds an adjective to the framework.

- Parameters:
  - `adjective`: The Adjective object to add.
- Returns: None

### rename_adjective(old_name: str, new_name: str) -> None

Renames an adjective in the framework.

- Parameters:
  - `old_name`: The current name of the adjective.
  - `new_name`: The new name for the adjective.
- Returns: None
- Raises: ValueError if no adjective with old_name is found.

### get_adjective(name: str) -> Adjective

Retrieves an adjective from the framework.

- Parameters:
  - `name`: The name of the adjective to retrieve.
- Returns: The Adjective object with the given name.
- Raises: KeyError if no adjective with the given name is found.

### configure_settings(settings_dict: Dict) -> None

Configures settings using a dictionary.

- Parameters:
  - `settings_dict`: A dictionary of settings to configure.
- Returns: None

# Settings

The ArgumentationFramework class includes settings for controlling explanation depth and verbosity:

```python
settings = {
            'explanation_depth': 3 ,
            'assumptions_verbosity': 'no'
        }

knowledgebase.configure_settings(settings)
```
## explanation_depth
Sets the depth of explanations, how deep towards the assumptions it should go.

## assumptions_verbosity
Set to 'verbose', 'minimal' or 'no'.
Sets how much of the assumptions to print.

# Adjectives

There are several types of adjectives:

## BooleanAdjective

Represents a boolean attribute of a node.

```python
BooleanAdjective(name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None)
```

- `name`: The name of the adjective.
- `definition`: The corresponding node attribute (default: DEFAULT_GETTER).
- `explanation`: An explanation for the adjective (optional).

## PointerAdjective

Represents an attribute that points to a specific value or node.

```python
PointerAdjective(name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None)
```

- `name`: The name of the adjective.
- `definition`: The corresponding node attribute (default: DEFAULT_GETTER).
- `explanation`: An explanation for the adjective (optional).

## ComparisonAdjective

Used for comparing nodes based on a specific attribute.

```python
ComparisonAdjective(name: str, property_pointer_adjective_name: str, operator: str)
```

- `name`: The name of the adjective.
- `property_pointer_adjective_name`: The name of the pointer adjective to use for comparison.
- `operator`: The comparison operator (e.g., ">", "<", "==").

## MaxRankAdjective

Represents the maximum rank in a group based on a comparison.

```python
MaxRankAdjective(name: str, comparison_adjective_name: str, group_pointer_adjective_name: str)
```

- `name`: The name of the adjective.
- `comparison_adjective_name`: The name of the comparison adjective to use.
- `group_pointer_adjective_name`: The name of the pointer adjective that selects the group to compare with.

## MinRankAdjective

Represents the minimum rank in a group based on a comparison.

```python
MinRankAdjective(name: str, comparison_adjective_name: str, group_pointer_adjective_name: str)
```

- `name`: The name of the adjective.
- `comparison_adjective_name`: The name of the comparison adjective to use.
- `group_pointer_adjective_name`: The name of the pointer adjective that selects the group to compare with.

# Explanations

Explanations provide reasoning for adjective assignments. Here are the available explanation classes:

## Assumption

```python
Assumption(description: str, definition: str = None)
```

A basic explanation based on an assumption.

- `description`: A string describing the assumption.
- `definition`: An optional string providing additional definition (default: None).

## Possession

```python
Possession(*args)
```

Explains by referring to another adjective's possession.

Usage:
- `Possession(adjective_name)`
- `Possession(pointer_adjective_name, adjective_name)`

- `adjective_name`: The name of the adjective to explain.
- `pointer_adjective_name`: Optional. The name of the pointer adjective that selects the object.

## Comparison

```python
Comparison(comparison_adjective_name: str, node_pointer_adjective_name: str)
```

Explains by comparing with another node.

- `comparison_adjective_name`: The name of the comparison adjective.
- `node_pointer_adjective_name`: The name of the pointer adjective that selects the object to compare with.

## GroupComparison

```python
GroupComparison(comparison_adjective_name: str, group_pointer_adjective_name: str, positive_implication: bool = True)
```

Explains by comparing with a group of nodes.

- `comparison_adjective_name`: The name of the comparison adjective.
- `group_pointer_adjective_name`: The name of the pointer adjective that selects the group to compare with.
- `positive_implication`: Whether the implication is positive (default: True).

## ConditionalExplanation

```python
ConditionalExplanation(condition: If, explanation_if_true: Explanation, explanation_if_false: Explanation)
```

Provides different explanations based on a condition.

- `condition`: A If object that determines which explanation to use.
- `explanation_if_true`: The explanation to use when the condition is true.
- `explanation_if_false`: The explanation to use when the condition is false.

## CompositeExplanation

```python
CompositeExplanation(*explanations: Explanation)
```

Combines multiple explanations.

- `*explanations`: Variable number of Explanation objects to be combined.

## If

```python
If(*args, value: Any = True)
```

Represents a condition based on an adjective's value.

Usage:
- `If("adjective_name")`
- `If("pointer_adjective_name", "adjective_name")`
- `If("pointer_adjective_name", "adjective_name", value=some_value)`

- `adjective_name`: The name of the adjective to check.
- `pointer_adjective_name`: Optional. The name of the pointer adjective that selects the object to check.
- `value`: The expected value of the adjective (default: True).