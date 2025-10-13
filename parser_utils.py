# parser_utils.py
import re

def tokenize(text):
    """Breaks the SECS message text into a stream of tokens."""
    token_specification = [
        ('LIST_START', r'<\s*L\s*\[\d+\]\s*>'),
        ('LIST_END',   r'>'),
        ('ASCII',      r"<\s*A\s*\[\d+\]\s*'([^']*)'\s*>"),
        ('UINT',       r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>"),
        ('SKIP',       r'[\s\n]+'), # Skip whitespace
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    tokens = []
    for mo in re.finditer(tok_regex, text):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == 'SKIP':
            continue
        elif kind == 'LIST_END':
            tokens.append(('LIST_END', '>'))
        elif kind == 'LIST_START':
            tokens.append(('LIST_START', value))
        else: # ASCII or UINT
            tokens.append((kind, value))
    return tokens

def build_tree(tokens):
    """Builds a nested Python list from a stream of tokens."""
    stack = [[]]
    for kind, value in tokens:
        if kind == 'LIST_START':
            new_list = []
            stack[-1].append(new_list)
            stack.append(new_list)
        elif kind == 'LIST_END':
            if len(stack) > 1:
                stack.pop()
        else: # ASCII or UINT
            stack[-1].append(value)
    return stack[0]
