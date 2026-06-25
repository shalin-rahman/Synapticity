"""
Text formatting utilities for cleaning AI output.
"""
import re

def strip_markdown_backticks(content: str) -> str:
    """
    Strips ```python ... ``` and ``` ... ``` blocks from AI output.
    Returns the inner raw code.
    """
    # Normalise Windows CRLF so the regex works regardless of LLM line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Match opening fence + optional language tag + optional trailing whitespace + newline
    pattern = re.compile(r"```[ \t]*(?:\w+)?[ \t]*\n([\s\S]+?)```")
    match = pattern.search(content)
    if match:
        return match.group(1).strip()

    # Fallback: strip raw backtick sequences but preserve the code content
    stripped = re.sub(r"```\w*", "", content).strip()
    return stripped
