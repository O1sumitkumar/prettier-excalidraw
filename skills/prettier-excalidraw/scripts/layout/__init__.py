"""Auto-layout for prettier-excalidraw specs. See README.md in this folder.

Public entry point (wired up in #52):

    from layout import layout
    spec = layout(spec, measure)   # fills in missing x/y; explicit coordinates win
"""
from .graph import Graph, Node, Edge, Container, from_spec, direction  # noqa: F401
from .rank import rank  # noqa: F401


def layout(spec, measure):
    """Fill in missing x/y on spec elements. Stages are implemented in #48-#52."""
    raise NotImplementedError("auto-layout stages are not implemented yet; see layout/README.md (#9)")
