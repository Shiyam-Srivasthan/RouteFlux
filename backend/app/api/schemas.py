"""Pydantic request/response models for the API layer.

Kept separate from app.models (the domain dataclasses used by the routing
engine) so the wire format can evolve independently of internal types.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AlgorithmName(str, Enum):
    dijkstra = "dijkstra"
    astar = "astar"


class GraphGenerateRequest(BaseModel):
    rows: int = Field(default=20, ge=1, le=100)
    cols: int = Field(default=20, ge=1, le=100)
    seed: int = 42


class NodeOut(BaseModel):
    id: int
    x: float
    y: float


class RoadOut(BaseModel):
    source: int
    destination: int
    distance: float
    speed: float
    congestion_multiplier: float
    is_open: bool
    effective_time: float


class GraphOut(BaseModel):
    nodes: list[NodeOut]
    roads: list[RoadOut]


class RouteRequest(BaseModel):
    source: int
    destination: int
    algorithm: AlgorithmName = AlgorithmName.dijkstra


class RouteResponse(BaseModel):
    path: list[int]
    cost: Optional[float]
    reachable: bool
    nodes_explored: int
    runtime_ms: float
    algorithm: str


class TrafficUpdateRequest(BaseModel):
    source: int
    destination: int
    multiplier: float = Field(ge=1.0)
    bidirectional: bool = False


class RoadActionRequest(BaseModel):
    source: int
    destination: int
    bidirectional: bool = False
