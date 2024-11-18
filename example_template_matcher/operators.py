# operators.py

def multi_swap(statement, swaps):
    """Swaps multiple characters in a string."""
    # Create unique temporary placeholders
    temp_placeholders = [f"_TEMP_{i}_" for i in range(len(swaps))]
    
    # First pass: replace each item in swaps with a unique placeholder
    for (old, _), temp in zip(swaps, temp_placeholders):
        statement = statement.replace(old, temp)
    
    # Second pass: replace each placeholder with its final swap value
    for (_, new), temp in zip(swaps, temp_placeholders):
        statement = statement.replace(temp, new)
    
    return statement

def negate_inequality(statement: str) -> str:
    """
    Negates an inequality.
    """
    swaps = [("≤", ">"), (">", "≤"), ("≥", "<"), ("<", "≥")]

    return multi_swap(statement, swaps)

def find_set(statement: str) -> str:
    """Finds and returns the first set expression enclosed in curly braces {}."""
    stack = []
    start_index = -1
    for i, char in enumerate(statement):
        if char == '{':
            if not stack:
                start_index = i
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack and start_index != -1:
                    return statement[start_index:i+1]
    return ""