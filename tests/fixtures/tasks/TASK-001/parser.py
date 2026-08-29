import re

def parse_regex_tokens(pattern: str) -> list[str]:
    """Parse regex pattern into individual tokens."""
    tokens = []
    i = 0
    while i < len(pattern):
        if pattern[i] == '\\' and i + 1 < len(pattern):
            tokens.append(pattern[i:i+2])
            i += 2
        elif pattern[i] in '[](){}*+?^$|':
            tokens.append(pattern[i])
            i += 1
        else:
            tokens.append(pattern[i])
            i += 1
    return tokens
