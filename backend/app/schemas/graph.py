from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Node category, e.g. student, alumni, skill, company, project")
    label: str = Field(..., description="Human-readable label for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Safe, non-private node properties")

class GraphEdge(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type, e.g. HAS_SKILL, WORKED_AT, MENTORED_BY")
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
