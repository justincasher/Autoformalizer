# translate_file.py

import json
from file_cleaner import *
from statement_translator import StatementTranslator 
from statement_stack import StatementStack
from text_compiler import compile_output

def main(file_path: str, templates_path: str):
    # Load the Lean file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return
    except IOError as e:
        print(f"An error occurred while reading the file: {e}")
        return
    
    # Load the templates
    with open(templates_path, 'r', encoding='utf-8') as file:
        templates = json.load(file)
    template_dict = {template["expression"]: template for template in templates}

    # Step 1: Remove unneeded text

    # Remove comments
    content = remove_lean_comments(content)

    # Remove specified lines
    words_to_remove = ["import", "open", "namespace", "end", "section"]
    content = remove_specific_lines(content, words_to_remove)

    # Remove forward/backward markets
    content = remove_direction_markers(content)

    # Step 2: Clean up syntax
    content = replace_succ_with_increment(content)

    # Step 3: Extract statements
    statement_keywords = ["theorem", "lemma", "definition"]
    statements = extract_statements(content, statement_keywords)

    # Step 4: Translate statements
    statement_translator = StatementTranslator(template_dict)
    translated_statements = []
    for i in range(len(statements)):
        # Translate each statement
        statement = statements[i]
        translated_statement = statement_translator(statement)
        translated_statements.append(translated_statement)

    # Step 5: Fix intro statements
    translated_statements = replace_intro_variable(translated_statements)

    # Step 6: Clean up the output
    cleaned_statements = clean_output(translated_statements)

    # Step 7: Compile the output into LaTeX
    compiled_text = compile_output(cleaned_statements)

    # Print the statements
    for i in range(len(cleaned_statements)):
        print("\n")
        print(statements[i])
        print("\n")
        print(cleaned_statements[i])

    print("\n")
    print(compiled_text)

    # Step 7: Compile new file

if __name__ == "__main__":
    # Set the file path here directly
    file_path = r"/Users/justinasher/Desktop/symbol_translator_4/lean_example.lean"
    templates_path = r"/Users/justinasher/Desktop/symbol_translator_4/templates.json"
    main(file_path, templates_path)