"""F20／F46 prototype: Markdown links read by a real parser (P1 slice 4).

verify_bootstrap.py finds links with a regular expression because A4 must run
without third-party packages. This module reads the same documents with
markdown-it-py (CommonMark plus tables), which understands what a regex does
not: reference-style links, parentheses inside a target, escaped brackets,
links inside code or HTML. ``uv run pytest`` uses it as an independent second
check of the repo's documents; it does not replace the A4 check.

Needs ``markdown-it-py`` (locked in uv.lock), so nothing A4 runs imports it.
"""
from pathlib import Path
from urllib.parse import unquote

from markdown_it import MarkdownIt

PARSER = MarkdownIt('commonmark').enable('table')
EXTERNAL = ('http://', 'https://', 'mailto:', '#')


def links(text):
    """Every link and image target in document order, as written."""
    found = []
    for token in PARSER.parse(text):
        for child in token.children or ():
            if child.type == 'link_open':
                found.append(child.attrGet('href'))
            elif child.type == 'image':
                found.append(child.attrGet('src'))
    return [target for target in found if target is not None]


def local_target(target):
    """The repo-relative file a link points at, or None for external and in-page links."""
    if not target or target.startswith(EXTERNAL) or '://' in target:
        return None
    path = unquote(target.split('#', 1)[0])
    return path or None


def dead_links(root, documents, skip=lambda document, target: False):
    """'document → target' for each local link whose file does not exist."""
    root = Path(root)
    dead = []
    for document in documents:
        base = (root / document).parent
        for target in links((root / document).read_text(encoding='utf-8')):
            path = local_target(target)
            if path is None or skip(document, path):
                continue
            if not (base / path).exists():
                dead.append('%s → %s' % (document, target))
    return dead
