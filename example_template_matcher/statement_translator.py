# statement_translator.py

from copy import deepcopy as dc
import re
import operators
from statement_stack import StatementStack

######################
## CALLED FUNCTIONS ##
######################

class StatementTranslator:

    def __init__(self, template_dict: dict):
        self.template_dict = template_dict
        self.statement_stack = StatementStack()
        self.left_right_pairs = [("(", ")"), ("{", "}")]

    def __call__(self, statement: str):
        # Keep track of how many spaces each line leads with
        leading_spaces = []
        for line in statement.strip().splitlines():
            space_count = len(line) - len(line.lstrip())
            leading_spaces.append(space_count)

        # Start by tokenizing our statement for template matching
        tokenized_statement = self.tokenize_statement(statement)
        
        # Next apply template matching to each line
        output = ""
        for i in range(len(tokenized_statement)):
            # Extract line, next line, amount of white space
            line = tokenized_statement[i]
            if i < len(tokenized_statement) - 1:
                next_line = tokenized_statement[i+1]
            else:
                next_line = None
            spaces = leading_spaces[i]
            
            # Translate
            translated_line = self.match_templates(line, next_line, spaces)

            # Make sure to include white space when printing
            if translated_line:
                output += " " * leading_spaces[i] + translated_line
                if i < len(tokenized_statement) - 1:
                    output += "\n"

        return output


    ##################
    ## TOKENIZATION ##
    ##################

    def tokenize_line(self, line: str) -> list:
        """Tokenize a single line, treating sub-expressions and commas as single tokens."""

        tokens = []
        i = 0
        while i < len(line):
            # Skip leading whitespace
            if line[i].isspace():
                i += 1
                continue

            # Check if the character is a comma
            if line[i] == ",":
                tokens.append(",")  # Add comma as a separate token
                i += 1
                continue

            # Check if the character matches any of the left delimiters
            match = None
            for left, right in self.left_right_pairs:
                if line[i] == left:
                    match = (left, right)
                    break

            if match:
                # Find the closing delimiter for the sub-expression
                left, right = match
                start_index = i
                depth = 1
                i += 1  # Move past the opening delimiter

                while i < len(line) and depth > 0:
                    if line[i] == left:
                        depth += 1  # Nested opening
                    elif line[i] == right:
                        depth -= 1  # Closing

                    i += 1

                # Extract and recursively translate the contents within the delimiters
                inner_expression = line[start_index + 1 : i - 1]  # Exclude delimiters
                translated_inner = self(inner_expression)
                tokens.append(f"{left}{translated_inner}{right}")  # Treat as one token
            else:
                # For non-delimiter tokens, accumulate characters until whitespace, comma, or delimiter
                start_index = i
                while i < len(line) and not line[i].isspace() and line[i] != "," and all(line[i] != l for l, _ in self.left_right_pairs):
                    i += 1

                tokens.append(line[start_index:i])  # Add non-delimiter token

        return tokens

    def tokenize_statement(self, statement: str) -> list:
        """Tokenize the statement into lines, each treated as a list of tokens."""
        tokenized_lines = []
        for line in statement.strip().splitlines():
            # Tokenize each line individually
            tokens = self.tokenize_line(line)
            if tokens:
                tokenized_lines.append(tokens)
        return tokenized_lines


    #######################
    ## TEMPLATE MATCHING ##
    #######################

    def match_templates(self, tokenized_line: list, tokenized_next_line: list = None, spaces: int = -1) -> str:
        """Apply template matching to a tokenized line based on the provided templates."""
        
        # Update the statement_stack to match the current scope
        if spaces != -1:
            self.statement_stack.prune_stack(spaces)

        output = []

        # Keep track of what is added to statement stack, so we do not replace 
        # a name with its value on the same line
        recently_added = []

        # Case 1: Existential constructions            
        if tokenized_line[0][0] == "⟨":
            # Step 1: CLean up line
            tokenized_line[0] = tokenized_line[0].lstrip('⟨')
            tokenized_line[-1] = tokenized_line[-1].rstrip('⟩')
            tokenized_line = [token for token in tokenized_line if token != ',']
            
            # Step 2: Replace statements with values and find tags
            values = []
            statement_tags = []
            for i in range(len(tokenized_line)):
                token = tokenized_line[i]
                item = self.statement_stack.get_by_name(token)
                if item:
                    values.append(item["statement"]) 
                    statement_tags.append(item["tag"])

            # Step 3: Construct output in a x, y, and z format
            output.append("finally, we have")
            output_list = [values[i] for i in range(len(values)) if statement_tags[i] not in ["let", "def"]]
            output.append(self.join_values(output_list))

            # Step 4: Update relevant statements
            name = self.statement_stack.get_prev_name_by_spacing(spaces-2)
            self.statement_stack.edit_item_by_name(name, exists=dc(values))
            self.statement_stack.edit_item_by_name(name, exists_tags=dc(statement_tags))
            
            # Clear tokenized line to prevent printing twice
            tokenized_line = []

        # Case 2: exact 
        if tokenized_line and tokenized_line[0] == "exact":
            # Step 1: Extract hypotheses
    
            # Skip over "exact"
            tokenized_line = tokenized_line[1:]

            # Check if tokenized line still exists
            if not tokenized_line:
                if tokenized_next_line:
                    return "we conclude the proof by"
                else:
                    return "we conclude the proof"

            # Remove brackets
            tokenized_line[0] = tokenized_line[0].lstrip('⟨')
            tokenized_line[-1] = tokenized_line[-1].rstrip('⟩')
            tokenized_line = [token for token in tokenized_line if token != ',']

            # Step 2: Substitute hypotheses
            values = []
            for i in range(len(tokenized_line)):
                token = tokenized_line[i]
                item = self.statement_stack.get_by_name(token)
                # If token is definition, we can skip
                if item["tag"] in ["def", "let"]:
                   continue
                else:
                    values.append(item["statement"]) 
            
            # Step 3: Add line to output
            output.append("finally, we conclude by")
            output.append(self.join_values(values))

            # We are done with tokenized_line
            tokenized_line = []

        # Case 3: rw
        if tokenized_line and tokenized_line[0] == "rw":
            # Remove "rw" and brackets, then leave it for later
            tokenized_line = tokenized_line[1:]
            tokenized_line[0] = tokenized_line[0].lstrip('[')
            tokenized_line[-1] = tokenized_line[-1].rstrip(']')

        # Case 4: intro
        if tokenized_line and tokenized_line[0] == "intro":
            # We will handle these later
            return " ".join(tokenized_line)

        # Case 5: lemma, theorem, have, etc. 
        tags = ["lemma", "theorem", "have"]
        if tokenized_line and tokenized_line[0] in tags: 
            tag = tokenized_line[0]
            name = tokenized_line[1]

            # Step 1: Append tag and statement name
            if tag != "have":
                output.extend([tag, name])
            # If have statement, only append "we claim"
            else: 
                output.append("we claim")
            
            # Discard tag and statement name
            tokenized_line = tokenized_line[2:]

            # Step 2: Create let statements
            assumptions = []

            # Iterate through the assumptions
            i = 0
            while tokenized_line[i] != ":":
                assumptions.append(tokenized_line[i])
                i += 1

            # Append assumptions to output
            if i != 0:
                assumption_string = self.match_assumptions(assumptions, tag)
                output.append(assumption_string)
                output.append("Then")

            # Skip over colon
            tokenized_line = tokenized_line[i+1:]

            # Step 3: Translate statement
            tokenized_statement = []

            # Iterate until proof
            i = 0 
            while i < len(tokenized_line) and tokenized_line[i] != ":=":
                tokenized_statement.append(tokenized_line[i])
                i += 1

            # Translate the statement
            statement_string = self.match_templates(tokenized_statement)
            output.append(statement_string)

            # Skip over ":="
            tokenized_line = tokenized_line[i+1:]

            # Skip over "by"
            if tokenized_line and tokenized_line[0] == "by":
                tokenized_line = tokenized_line[1:]

            # Step 4: Translate proof
            if tokenized_line:
                output.append(", because")
            elif tag == "have":
                output.append(". Indeed,")

            # Add the statement to the statement stack
            item = {
                "spaces": spaces,
                "tag": tag,
                "name": name,
                "assumes": assumptions,
                "statement": statement_string
            }
            self.statement_stack.add_to_stack(item)
            recently_added.append(name) 

        # Case 6: let 
        if tokenized_line and tokenized_line[0] == "let":
            # Step 1: Make initial let upper case
            output.append("let")
            tokenized_line = tokenized_line[1:]

            # Step 2: Translate L.H.S.
            lhs = []

            # End of L.H.S. is denoted by ":="
            i = 0 
            while i < len(tokenized_line) and tokenized_line[i] != ":=":
                lhs.append(tokenized_line[i])
                i += 1

            # Add translated L.H.S
            translated_lhs = self.match_templates(lhs)
            output.append(translated_lhs)

            # Skip over ":=" and replace it with "be"
            tokenized_line = tokenized_line[i+1:]
            output.append("be")

            # Step 3: Translate the R.H.S.
            translated_rhs = self.match_templates(tokenized_line)
            output.append(translated_rhs)

            # Prevent printing twice
            tokenized_line = []

            # Step 4: Add definition to statement_stack
            item = {
                "spaces": spaces,
                "tag": "let",
                "name": lhs[0],
                "statement": f"{lhs[0]} is {translated_rhs}"
            }
            self.statement_stack.add_to_stack(item)

        # Case 7: obtain
        if tokenized_line and tokenized_line[0] == "obtain": 
            # Skip over obtain
            tokenized_line = tokenized_line[1:]

            # Step 1: Extract variables from ⟨ ⟩
            names = []
            i = 0

            # Look for tokens until we reach ":="
            while i < len(tokenized_line) and tokenized_line[i] != ':=':
                # Remove brackets and commas, adding only variable names to the list
                token = tokenized_line[i].strip("⟨⟩,")
                if token:
                    names.append(token)
                i += 1

            # Step 2: Move past ":=" and identify the theorem name
            if i < len(tokenized_line) and tokenized_line[i] == ':=':
                tokenized_line = tokenized_line[i + 1:]
            underlying_theorem = tokenized_line[0]
            tokenized_line = tokenized_line[1:]

            # Step 3: Retrieve theorem details from the stack
            statement_item = self.statement_stack.get_by_name(underlying_theorem)
            assumes = statement_item.get('assumes', [])
            exists_list = statement_item.get('exists', [])
            tags = statement_item.get('exists_tags', [])

            # Step 4: Create substitution map from assumptions to provided arguments
            variable_names = [re.match(r'\((\w+)\s*:', a).group(1) for a in assumes]
            substitutions = dict(zip(variable_names, tokenized_line))

            # Step 5: Apply substitutions to each statement in the "exists" list
            substituted_exists = [
                re.sub(rf'\b{re.escape(var)}\b', arg, stmt)
                for stmt in exists_list
                for var, arg in substitutions.items()
            ]

            # Step 6: Ensure names and statements match in number
            if len(substituted_exists) != len(names):
                raise ValueError(
                    f"Number of substituted exists statements ({len(substituted_exists)}) does not match number of names ({len(names)})."
                )

            # Step 7: Add each name and its statement to the statement stack
            statements = substituted_exists
            for name, stmt, tag in zip(names, statements, tags):
                item = {
                    "spaces": spaces,
                    "tag": tag,
                    "name": name,
                    "statement": stmt
                }
                self.statement_stack.add_to_stack(item)
            
            # Step 8: Add results to output
            output.append(f"by {underlying_theorem}, there exists")
            output.append(", ".join(statements[:-1]))
            output.append((", and " if len(statements) > 1 else ""))
            output.append(statements[-1])

            # Clear tokenized_line to prevent further processing
            tokenized_line = []

        # Case 8: General 
        i = 0
        while i < len(tokenized_line):
            # First apply template matching
            formatted_token = ""
            token = tokenized_line[i]

            # Check if the token is a template, or if we need to trim it and check again
            if token in self.template_dict:
                template_key = token
            else:
                # Split the token on the first period, if it exists, and check the remainder
                template_key = token.split('.', 1)[-1] if '.' in token else token

            # Determine if the (possibly trimmed) token has a template
            if template_key in self.template_dict:
                # Get the template
                template_info = self.template_dict[template_key]
                template = template_info["template"]
                num_args = template_info["variables"]

                # Collect necessary arguments if specified
                args = tokenized_line[i+1:i+1+num_args]

                # Apply the template, filling placeholders if needed
                for j, arg in enumerate(args):
                    template = template.replace(f"{{{j}}}", str(arg))
                formatted_token = template

                # Skip over arguments
                i += num_args
            else:
                # If no template is found, treat it as a standalone token
                formatted_token = token

            # Add formatted token to output and move on to the next token
            output.append(formatted_token)
            i += 1  

        # Create an output string
        output_str = " ".join(output)

        # Case 9: {s1, negateInequality}
        matches = list(re.finditer(r"\{s\d+(?:,\s*)?[^\}]+\}", output_str))
        for match in reversed(matches):
            # Extract the matched string
            matched_text = match.group()
            
            # Apply the operation or retrieve the statement using apply_operation
            result = self.apply_operation(matched_text)
            
            # Substitute the result into the output string at the current match position
            output_str = output_str[:match.start()] + result + output_str[match.end():]

        # Case 10: fun h =>
        match = re.search(r"\bfun\s+(\w+)\s*=>", output_str)
        if match:
            # Split up string 
            before_fun = output_str[:match.start()].strip().rstrip(".")
            name = match.group(1)
            
            # Add to statement stack
            item = {
                "spaces": spaces,
                "tag": "fun",
                "name": name,
                "statement": before_fun
            }
            self.statement_stack.add_to_stack(item)

            # Remove text
            output_str = before_fun

        # Case 11: Unmatched statements
        words = output_str.split()
        replaced_words = []

        for i, word in enumerate(words):
            # Get the statement values, ignoring let and def
            replacement = self.statement_stack.get_statement_by_name(word, ignore_defs=True)
            
            # Add "and" before replacement if output already has text
            if replacement and word not in recently_added:
                if replaced_words:  # Check if there's existing text before the replacement
                    replaced_words.append("and")
                replaced_words.append(replacement)
            else:
                replaced_words.append(word)

        output_str = " ".join(replaced_words)

        # Join the output list into a readable sentence
        return output_str

    def match_assumptions(self, assumptions: list, tag: str):
        # Parse assumptions once
        parsed_assumptions = []
        for assumption in assumptions:
            var, typ = assumption.strip('()').split(' : ')
            parsed_assumptions.append(f"{var} be in {typ}")

        # Format based on the tag

        # Case 1: theorem, lemma, etc.
        tags_case_1 = ["lemma", "theorem"]
        if tag in tags_case_1:
            return "Let " + ", and let ".join(parsed_assumptions) + "."

        # Case 2: have
        elif tag == "have":
            return ", assuming " + ", ".join(parsed_assumptions) + ","

        # Case 3: unknown
        else: 
            return "Unknown tag"
        
    def apply_operation(self, command: str) -> str:
        """Apply an operation to a specified statement or return the statement itself if no operation is given."""
        
        # Match the command format
        match = re.match(r"\{(s(\d+))(?:,\s*(\w+))?\}", command)
        if not match:
            raise ValueError(f"Invalid command format: {command}")
        
        statement_ref, index_str, operation_name = match.groups()
        index = int(index_str)

        # Retrieve the statement from the stack
        try:
            statement = self.statement_stack.peek_n(index)
        except IndexError as e:
            raise ValueError(f"Stack does not contain s{index}: {e}")

        # If no operation is specified, return the statement directly
        if not operation_name:
            return statement

        # Get the method from operations.py by name
        if not hasattr(operators, operation_name):
            raise AttributeError(f"Operation '{operation_name}' not found in operations module")

        operation = getattr(operators, operation_name)
        
        # Apply the operation to the statement
        result = operation(statement)

        return result
    

    ###############
    ## Utilities ##
    ###############

    def join_values(self, values):
        if not values:
            return ""  # Return an empty string if the list is empty
        elif len(values) == 1:
            return values[0]  # Return the single element if there's only one
        elif len(values) == 2:
            return " and ".join(values)  # Join with "and" if there are two items
        else:
            # For 3 or more items, join all but the last with commas, and add "and" before the last
            return ", ".join(values[:-1]) + ", and " + values[-1]