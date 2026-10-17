from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.graph import GraphResponse
from app.services.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

@router.get("/me", response_model=GraphResponse, status_code=status.HTTP_200_OK)
async def get_my_knowledge_graph(
    depth: int = Query(2, ge=1, le=3, description="Traversal depth"),
    max_nodes: int = Query(40, ge=5, le=100, description="Max node bound"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve the current user's authorized professional knowledge graph."""
    return await graph_service.get_user_graph(
        user_id=current_user["id"],
        depth=depth,
        max_nodes=max_nodes,
    )
