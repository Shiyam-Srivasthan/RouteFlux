"""API endpoints for RouteFlux.

Graph state is a single in-memory Graph held on app.state.graph (no DB —
out of scope for this project). POST /graph/generate creates/replaces it;
every other endpoint operates on whatever graph currently exists there.
"""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas import (
    GraphGenerateRequest,
    GraphOut,
    NodeOut,
    RoadActionRequest,
    RoadOut,
    RouteRequest,
    RouteResponse,
    TrafficUpdateRequest,
)
from app.generator import generate_grid_graph
from app.graph import Graph
from app.services.routing import compute_route
from app.services.traffic import close_road, open_road, update_congestion

router = APIRouter()


def get_graph(request: Request) -> Graph:
    graph = request.app.state.graph
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph has been generated yet. Call POST /graph/generate first.")
    return graph


def _to_graph_out(graph: Graph) -> GraphOut:
    return GraphOut(
        nodes=[NodeOut(id=n.id, x=n.x, y=n.y) for n in graph.nodes.values()],
        roads=[
            RoadOut(
                source=r.source,
                destination=r.destination,
                distance=r.distance,
                speed=r.speed,
                congestion_multiplier=r.congestion_multiplier,
                is_open=r.is_open,
                effective_time=r.effective_time,
            )
            for r in graph.roads
        ],
    )


@router.post("/graph/generate", response_model=GraphOut)
def generate_graph_endpoint(payload: GraphGenerateRequest, request: Request) -> GraphOut:
    graph = generate_grid_graph(rows=payload.rows, cols=payload.cols, seed=payload.seed)
    request.app.state.graph = graph
    return _to_graph_out(graph)


@router.get("/graph", response_model=GraphOut)
def get_graph_endpoint(graph: Graph = Depends(get_graph)) -> GraphOut:
    return _to_graph_out(graph)


@router.post("/route", response_model=RouteResponse)
def route_endpoint(payload: RouteRequest, graph: Graph = Depends(get_graph)) -> RouteResponse:
    try:
        result = compute_route(graph, payload.source, payload.destination, algorithm=payload.algorithm.value)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    reachable = len(result.path) > 0
    return RouteResponse(
        path=result.path,
        cost=result.cost if reachable else None,
        reachable=reachable,
        nodes_explored=result.nodes_explored,
        runtime_ms=result.runtime_ms,
        algorithm=result.algorithm,
    )


@router.post("/traffic/update", response_model=GraphOut)
def traffic_update_endpoint(payload: TrafficUpdateRequest, graph: Graph = Depends(get_graph)) -> GraphOut:
    try:
        update_congestion(graph, payload.source, payload.destination, payload.multiplier, bidirectional=payload.bidirectional)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_graph_out(graph)


@router.post("/road/close", response_model=GraphOut)
def road_close_endpoint(payload: RoadActionRequest, graph: Graph = Depends(get_graph)) -> GraphOut:
    try:
        close_road(graph, payload.source, payload.destination, bidirectional=payload.bidirectional)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_graph_out(graph)


@router.post("/road/open", response_model=GraphOut)
def road_open_endpoint(payload: RoadActionRequest, graph: Graph = Depends(get_graph)) -> GraphOut:
    try:
        open_road(graph, payload.source, payload.destination, bidirectional=payload.bidirectional)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_graph_out(graph)
