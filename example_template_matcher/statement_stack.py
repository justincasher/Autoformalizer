class StatementStack:
    """A simple stack implementation using a Python list."""

    def __init__(self):
        """Initialize an empty stack."""
        self.items = []

    def add_to_stack(self, item):
        """
        Add an item to the top of the stack.

        item = [depth, tag, name, value]
        """
        self.items.append(item)

    def prune_stack(self, spaces):
        """
        Remove items from the stack with a greater number of spaces than the provided value.
        """
        self.items = [existing_item for existing_item in self.items if existing_item['spaces'] <= spaces]

    def remove_from_stack(self):
        """Remove and return the top item from the stack."""
        if not self.is_empty():
            return self.items.pop()
        else:
            raise IndexError("remove_from_stack(): pop from empty stack")

    def is_empty(self):
        """Check if the stack is empty."""
        return len(self.items) == 0

    def peek(self):
        """Return the top item of the stack without removing it."""
        if not self.is_empty():
            return self.items[-1]
        else:
            raise IndexError("peek(): stack is empty")
        
    def peek_n(self, n):
        """Return the nth item from the top of the stack (s1 is top)."""
        if n <= len(self.items) and n > 0:
            return self.items[-n]['statement']
        else:
            raise IndexError(f"Cannot peek s{n}: stack has only {len(self.items)} items.")

    def size(self):
        """Get the number of items in the stack."""
        return len(self.items)
    
    def get_by_name(self, name):
        """Returns the underlying dictionary of the item with the specified name."""
        for item in self.items:
            if item['name'] == name:
               return item
        return None # Return None if not found
    
    def get_statement_by_name(self, name, ignore_defs=False):
        """Return the statement of the item with the specified name."""
        for item in self.items:
            if item['name'] == name:
                if not ignore_defs or item['tag'] not in ["let", "def"]:
                    return item['statement']
        return None # Return None if not found
    
    def get_prev_name_by_spacing(self, spaces):
        """Return the name of the previous item with the specified number of spaces, or None if no match."""
        for item in reversed(self.items):
            if item['spaces'] == spaces:
                return item['name']
        return None # Return None if not found
    
    def edit_item_by_name(self, name: str, **kwargs: dict[str, any]) -> bool:
        """Edit the properties of an item in the stack with the specified name."""
        for item in self.items:
            if item['name'] == name:
                for key, value in kwargs.items():
                    item[key] = value
                return True  # Indicate success
        return False  # Indicate failure if item with the specified name is not found

    def __str__(self):
        """Return a formatted string representation of the stack."""
        max_attr_length = max(len(attr) for item in self.items for attr in item)

        formatted_items = "\n".join(
            f"  Item {i + 1}:\n" +
            "\n".join(f"    {attr.capitalize():<{max_attr_length}}: {value}" for attr, value in item.items())
            for i, item in enumerate(self.items[::-1])
        )
         
        return f"Stack (top -> bottom):\n{formatted_items}"
