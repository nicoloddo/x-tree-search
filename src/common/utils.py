import itertools

def join_arrays_respective_elements(arr1, arr2):
    """
    Combine each element of the first array with the respective same position element(s) of the second array.

    Parameters:
    arr1 (list): First list of strings.
    arr2 (list): Second list of strings or lists.

    Returns:
    list: A list of lists containing combined elements.
    """
    if len(arr1) != len(arr2):
        raise ValueError("Both arrays must have the same length.")
    
    combined_array = []
    for a, b in zip(arr1, arr2):
        if isinstance(b, list):
            combined_element = [a] + b
        else:
            combined_element = [a, b]
        combined_array.append(combined_element)
    
    return combined_array

def flatten_list(list_input):
    return list(itertools.chain.from_iterable(list_input))