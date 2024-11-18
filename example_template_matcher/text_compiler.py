def compile_output(theorem_list):
    """Converts a list of structured theorem and proof statements into LaTeX formatted code."""
    output = []

    def process_line(line):
        """Capitalize the first letter and ensure the line ends with appropriate punctuation."""
        line = line.strip()
        if not line:
            return ''
        # Capitalize first character
        line = line[0].upper() + line[1:]
        # Check if the line ends with common punctuation
        if not line.endswith(('.', ',', ';', ':')):
            line += '.'
        return line

    for theorem_entry in theorem_list:
        lines = theorem_entry.split('\n')
        in_proof = False
        proof_paragraph = []  # Store all lines of the proof in a single paragraph

        for line in lines:
            stripped_line = line.lstrip()
            if not stripped_line:
                continue  # Skip empty lines

            if stripped_line.startswith("theorem"):
                if in_proof:
                    # Output the proof as a single paragraph
                    output.append("\\begin{proof}")
                    output.append(' '.join(proof_paragraph))
                    output.append("\\end{proof}\n")
                    # Reset proof state
                    proof_paragraph = []
                    in_proof = False

                # Process theorem line: "theorem name statement"
                parts = stripped_line.split(' ', 2)
                if len(parts) < 3:
                    continue  # Invalid theorem format, skip
                _, theorem_name, theorem_statement = parts
                output.append(f"\\begin{{theorem}}[{theorem_name}]")
                # Ensure the statement ends with appropriate punctuation
                theorem_statement = process_line(theorem_statement)
                output.append(theorem_statement)
                output.append("\\end{theorem}\n")

            elif line.lstrip():  # Any indented line is part of the proof
                if not in_proof:
                    in_proof = True  # Mark that we're inside a proof
                # Add the processed line to the proof paragraph
                proof_paragraph.append(process_line(stripped_line))

        # After processing all lines, check if there's an open proof
        if in_proof:
            output.append("\\begin{proof}")
            output.append(' '.join(proof_paragraph))  # Output the entire proof as a single paragraph
            output.append("\\end{proof}\n")

    # Combine all parts into the final LaTeX code
    return '\n'.join(output)
