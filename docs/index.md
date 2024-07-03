# Argumentation Framework API Documentation

## Index

1. [Introduction](#1-introduction)
2. [ArgumentationFramework](#2-argumentationframework)
   2.1 [Methods](#21-methods)
   2.2 [Settings](#22-settings)
3. [Adjectives](#3-adjectives)
   3.1 [BooleanAdjective](#31-booleanadjective)
   3.2 [PointerAdjective](#32-pointeradjective)
   3.3 [ComparisonAdjective](#33-comparisonadjective)
   3.4 [MaxRankAdjective](#34-maxrankadjective)
   3.5 [MinRankAdjective](#35-minrankadjective)
4. [Explanations](#4-explanations)
5. [Usage Example: Minimax Tree with Scoring](#5-usage-example-minimax-tree-with-scoring)
6. [Conclusion](#6-conclusion)

## 1. Introduction

The Argumentation Framework API provides a flexible system for defining propositions and inferences about nodes in a tree-based structure. By defining a tree search algorithm's reasoning behind nodes values, the framework can then be used to explain any decision made by the algorithm in an interactive argumentative way.

## 2. ArgumentationFramework

The main class that manages adjectives and their relationships.

```python
knowledgebase = ArgumentationFramework()
```

### 2.1 Methods

#### add_adjective(adjective: Adjective) -> None

Adds an adjective to the framework.

- Parameters:
  - `adjective`: The Adjective object to add.
- Returns: None

#### rename_adjective(old_name: str, new_name: str) -> None

Renames an adjective in the framework.

- Parameters:
  - `old_name`: The current name of the adjective.
  - `new_name`: The new name for the adjective.
- Returns: None
- Raises: ValueError if no adjective with old_name is found.

#### get_adjective(name: str) -> Adjective

Retrieves an adjective from the framework.

- Parameters:
  - `name`: The name of the adjective to retrieve.
- Returns: The Adjective object with the given name.
- Raises: KeyError if no adjective with the given name is found.

#### configure_settings(settings_dict: Dict) -> None

Configures settings using a dictionary.

- Parameters:
  - `settings_dict`: A dictionary of settings to configure.
- Returns: None

### 2.2 Settings

The ArgumentationFramework class includes settings for controlling explanation depth and verbosity:

```python
knowledgebase.explanation_depth = 5
knowledgebase.assumptions_verbosity = 'minimal'
knowledgebase.repeat_explanations = False
```

## 3. Adjectives

There are several types of adjectives:

### 3.1 BooleanAdjective

Represents a boolean attribute of a node.

```python
BooleanAdjective(name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None)
```

- `name`: The name of the adjective.
- `definition`: The corresponding node attribute (default: DEFAULT_GETTER).
- `explanation`: An explanation for the adjective (optional).

### 3.2 PointerAdjective

Represents an attribute that points to a specific value or node.

```python
PointerAdjective(name: str, definition: str = DEFAULT_GETTER, explanation: Explanation = None)
```

- `name`: The name of the adjective.
- `definition`: The corresponding node attribute (default: DEFAULT_GETTER).
- `explanation`: An explanation for the adjective (optional).

### 3.3 ComparisonAdjective

Used for comparing nodes based on a specific attribute.

```python
ComparisonAdjective(name: str, property_pointer_adjective_name: str, operator: str)
```

- `name`: The name of the adjective.
- `property_pointer_adjective_name`: The name of the pointer adjective to use for comparison.
- `operator`: The comparison operator (e.g., ">", "<", "==").

### 3.4 MaxRankAdjective

Represents the maximum rank in a group based on a comparison.

```python
MaxRankAdjective(name: str, comparison_adjective_name: str, group_pointer_adjective_name: str)
```

- `name`: The name of the adjective.
- `comparison_adjective_name`: The name of the comparison adjective to use.
- `group_pointer_adjective_name`: The name of the pointer adjective that selects the group to compare with.

### 3.5 MinRankAdjective

Represents the minimum rank in a group based on a comparison.

```python
MinRankAdjective(name: str, comparison_adjective_name: str, group_pointer_adjective_name: str)
```

- `name`: The name of the adjective.
- `comparison_adjective_name`: The name of the comparison adjective to use.
- `group_pointer_adjective_name`: The name of the pointer adjective that selects the group to compare with.

## 4. Explanations

Explanations provide reasoning for adjective assignments. Here are the available explanation classes:

### Assumption

```python
Assumption(description: str, definition: str = None)
```

A basic explanation based on an assumption.

- `description`: A string describing the assumption.
- `definition`: An optional string providing additional definition (default: None).

### Possession

```python
Possession(*args)
```

Explains by referring to another adjective's possession.

Usage:
- `Possession(adjective_name)`
- `Possession(pointer_adjective_name, adjective_name)`

- `adjective_name`: The name of the adjective to explain.
- `pointer_adjective_name`: Optional. The name of the pointer adjective that selects the object.

### Comparison

```python
Comparison(comparison_adjective_name: str, node_pointer_adjective_name: str)
```

Explains by comparing with another node.

- `comparison_adjective_name`: The name of the comparison adjective.
- `node_pointer_adjective_name`: The name of the pointer adjective that selects the object to compare with.

### GroupComparison

```python
GroupComparison(comparison_adjective_name: str, group_pointer_adjective_name: str, positive_implication: bool = True)
```

Explains by comparing with a group of nodes.

- `comparison_adjective_name`: The name of the comparison adjective.
- `group_pointer_adjective_name`: The name of the pointer adjective that selects the group to compare with.
- `positive_implication`: Whether the implication is positive (default: True).

### ConditionalExplanation

```python
ConditionalExplanation(condition: PossessionCondition, true_explanation: Explanation, false_explanation: Explanation)
```

Provides different explanations based on a condition.

- `condition`: A PossessionCondition object that determines which explanation to use.
- `true_explanation`: The explanation to use when the condition is true.
- `false_explanation`: The explanation to use when the condition is false.

### CompositeExplanation

```python
CompositeExplanation(*explanations: Explanation)
```

Combines multiple explanations.

- `*explanations`: Variable number of Explanation objects to be combined.

### PossessionCondition

```python
PossessionCondition(*args, value: Any = True)
```

Represents a condition based on an adjective's value.

Usage:
- `PossessionCondition("adjective_name")`
- `PossessionCondition("pointer_adjective_name", "adjective_name")`
- `PossessionCondition("pointer_adjective_name", "adjective_name", value=some_value)`

- `adjective_name`: The name of the adjective to check.
- `pointer_adjective_name`: Optional. The name of the pointer adjective that selects the object to check.
- `value`: The expected value of the adjective (default: True).

## 5. Usage Example: Minimax Tree with Scoring

Here's an example of how to use the Argumentation Framework API to represent a minimax tree with scoring:

```python
knowledgebase = ArgumentationFramework()

# Define "leaf" adjective
knowledgebase.add_adjective( 
    BooleanAdjective("leaf",
        definition = "node.is_leaf")
)

# Define "score" adjective
knowledgebase.add_adjective( 
    PointerAdjective("score",
        definition = "node.score",
        explanation = ConditionalExplanation(
            condition = PossessionCondition("leaf"),
            true_explanation = Assumption("Leaf nodes have scores from the evaluation function"),
            false_explanation = CompositeExplanation(
                Assumption("Internal nodes have scores from children"),
                Possession("backtracing child"))
        ))
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
            condition = PossessionCondition("opponent player turn"),
            true_explanation = CompositeExplanation(
                Assumption("We assume the opponent will do their best move."),
                Possession("backtracing child", "worst")),
            false_explanation = CompositeExplanation(
                Assumption("On our turn we take the maximum rated move."),
                Possession("backtracing child", "best"))
        ))
)

# Define "better" comparison adjective
knowledgebase.add_adjective(
    ComparisonAdjective("better", "score", ">")
)
```

## 6. Conclusion

The Argumentation Framework API provides a powerful tool for representing and reasoning about complex tree-based structures. By defining adjectives and their relationships, you can create sophisticated models for game theory, decision making, and other domains that involve tree-like structures with attributes and comparisons.
