#!/usr/bin/env python3
"""
Debug script to see how the decision prompt is being processed
"""

def load_decision_prompt_debug(filename: str = "gooby_decision.md") -> str:
    """
    Debug version of load_decision_prompt to see what's happening
    """
    from pathlib import Path

    decision_path = Path(filename)

    with open(decision_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    print("=== RAW CONTENT ===")
    print(repr(content[:200]) + "...")
    print()

    # Remove markdown headers and format for LLM
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        # Skip markdown headers, separators, and empty lines
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            cleaned_lines.append(line)

    print("=== CLEANED LINES ===")
    for i, line in enumerate(cleaned_lines[:10]):
        print(f"{i+1}: {repr(line)}")
    print("...")
    print()

    decision = ' '.join(cleaned_lines)

    print("=== JOINED RESULT ===")
    print(repr(decision[:200]) + "...")
    print()

    # Clean up extra spaces
    while '  ' in decision:
        decision = decision.replace('  ', ' ')

    print("=== FINAL RESULT ===")
    print(repr(decision[:200]) + "...")
    print()

    return decision

if __name__ == "__main__":
    result = load_decision_prompt_debug()
    print(f"Final length: {len(result)}")