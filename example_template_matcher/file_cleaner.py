# file_cleaner.py

import re

def remove_lean_comments(file_content: str) -> str:
    # Remove block comments (including multiline ones)
    file_content = re.sub(r"/-.*?-/", "", file_content, flags=re.DOTALL)

    # Remove single-line comments
    file_content = re.sub(r"--.*", "", file_content)

    # Remove any trailing whitespace resulting from comment removal
    file_content = re.sub(r"[ \t]+(\r?\n)", r"\1", file_content)

    # Clean up extra blank lines
    file_content = re.sub(r"\n\s*\n", "\n\n", file_content)

    return file_content

def remove_specific_lines(file_content: str, words_to_remove: list) -> str:
    # Create a regular expression to match lines starting with any of the specified words
    pattern = r"^\s*(" + "|".join(re.escape(word) for word in words_to_remove) + r")\b.*"
    
    # Remove lines matching the pattern
    file_content = re.sub(pattern, "", file_content, flags=re.MULTILINE)
    
    # Clean up extra blank lines left by the removals
    file_content = re.sub(r"\n\s*\n", "\n\n", file_content)

    return file_content

def remove_direction_markers(content):
    # Replace occurrences of ").1" and ").2" with ")"
    content = content.replace(").1", ")").replace(").2", ")")
    return content    

def extract_statements(file_content: str, keywords: list) -> list:
    statements = []
    current_statement = []
    in_statement = False
    keywords_pattern = re.compile(r"^\s*(" + "|".join(re.escape(word) for word in keywords) + r")\b")

    # Go through each line in the file content
    for line in file_content.splitlines():
        if keywords_pattern.match(line):  # Line starts with one of the keywords
            if in_statement:
                # Save the completed statement
                statements.append("\n".join(current_statement))
                current_statement = []
            in_statement = True
        if in_statement:
            current_statement.append(line)

    # Add the last statement if it exists
    if current_statement:
        statements.append("\n".join(current_statement))

    return statements

def clean_output(translated_statements):
    equation_symbols = ["+", "-", "*", "/", "="]  # Add other symbols as needed
    # Create a regex pattern that matches any of the equation symbols
    equation_symbols_pattern = "|".join(map(re.escape, equation_symbols))

    cleaned_statements = []
    for line in translated_statements:
        # Remove any parentheses without symbols from equation_symbols
        # This regex finds parentheses that don't contain any equation symbols
        cleaned_line = re.sub(r'\(([^()]*?)\)', 
                              lambda m: m.group(1) if not re.search(equation_symbols_pattern, m.group(1)) else m.group(0), 
                              line)

        # Remove redundant "because"
        cleaned_line = re.sub(r'(because\s+)+', 'because ', cleaned_line)

        # Remove "and" after "because"
        cleaned_line = re.sub(r'\bbecause\s+and\b', 'because', cleaned_line)

        # Remove spaces before commas and periods
        cleaned_line = re.sub(r'\s+([,.])', r'\1', cleaned_line)

        cleaned_statements.append(cleaned_line)
    return cleaned_statements

def replace_succ_with_increment(content: str) -> str:
    # Replace occurrences of `.succ` with `(x+1)`
    return re.sub(r"(\w+)\.succ", r"(\1+1)", content)

def replace_intro_variable(statements):
    updated_statements = []
    
    for statement in statements:
        lines = statement.splitlines()
        modified_lines = []
        for_every_stack = []
        
        for line in lines:
            # Track "for every VARIABLE_NAME" declarations
            for match in re.finditer(r"\bfor every (\w+)\b", line):
                for_every_stack.append(match.group(1))
            
            # Process "intro VARIABLE_NAME" to replace and remove it
            intro_match = re.search(r"\bintro (\w+)\b", line)
            if intro_match and for_every_stack:
                intro_var = intro_match.group(1)
                variable_name = for_every_stack.pop()
                
                # Replace VARIABLE_NAME in the most recent "for every" line
                for j in range(len(modified_lines)-1, -1, -1):
                    if re.search(rf"\bfor every {re.escape(variable_name)}\b", modified_lines[j]):
                        modified_lines[j] = re.sub(rf"\b{re.escape(variable_name)}\b", intro_var, modified_lines[j])
                        break
                continue  # Skip adding the "intro" line to remove it

            # Add non-"intro" lines to the output
            modified_lines.append(line)
        
        updated_statements.append("\n".join(modified_lines))
    
    return updated_statements