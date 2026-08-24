"""Dynamic traffic simulation: congestion updates and road open/close state.

Thin orchestration over Graph's mutation methods, which already own validation
(congestion_multiplier >= 1.0, road must exist). Roads are directed, so by
default these only affect the given (source, destination) direction; pass
bidirectional=True to mirror the change onto the reverse road if one exists.
"""
from app.graph import Graph
from app.models import CONGESTION_LEVELS


def update_congestion(graph: Graph, source: int, destination: int, multiplier: float, bidirectional: bool = False) -> None:
    graph.set_congestion(source, destination, multiplier)
    if bidirectional and graph.get_road(destination, source) is not None:
        graph.set_congestion(destination, source, multiplier)


def update_congestion_by_level(graph: Graph, source: int, destination: int, level: str, bidirectional: bool = False) -> None:
    if level not in CONGESTION_LEVELS:
        raise ValueError(f"Unknown congestion level '{level}'. Valid levels: {list(CONGESTION_LEVELS)}")
    update_congestion(graph, source, destination, CONGESTION_LEVELS[level], bidirectional=bidirectional)


def close_road(graph: Graph, source: int, destination: int, bidirectional: bool = False) -> None:
    graph.close_road(source, destination)
    if bidirectional and graph.get_road(destination, source) is not None:
        graph.close_road(destination, source)


def open_road(graph: Graph, source: int, destination: int, bidirectional: bool = False) -> None:
    graph.open_road(source, destination)
    if bidirectional and graph.get_road(destination, source) is not None:
        graph.open_road(destination, source)
