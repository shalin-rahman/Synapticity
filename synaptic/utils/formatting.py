"""
Text formatting utilities for agent output sanitization.
"""
import re

def strip_markdown_backticks(content: str) -> str:
    """
    Strips ```python ... ``` and ``` ... ``` blocks from AI output.
    Returns the inner raw code.
    """
    # Pattern for code blocks with optional language tag
    pattern = re.compile(r"```(?:\w+)?\n([\s\S]+?)```")
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    
    # Simple backtick strip if no block structure but backticks present
    return content.replace("```", "").strip()
