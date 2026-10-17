import logging
from typing import Any, Dict, List, Set
import networkx as nx
from app.core.exceptions import AppException
from app.repositories.mentorship_repository import mentorship_repo
from app.repositories.profile_repository import profile_repo
from app.repositories.user_repository import user_repo
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse

logger = logging.getLogger(__name__)

class GraphService:
    async def get_user_graph(self, user_id: str, depth: int = 2, max_nodes: int = 40) -> GraphResponse:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found.",
                status_code=404,
            )

        user_profile = await profile_repo.get_by_user_id(user_id)
        if not user_profile:
            raise AppException(
                code="PROFILE_NOT_FOUND",
                message="User profile required for knowledge graph.",
                status_code=404,
            )

        G = nx.Graph()

        # Add central user node
        center_node_id = f"user_{user_id}"
        role = user.get("role", "student")
        G.add_node(
            center_node_id,
            id=center_node_id,
            type=role,
            label=user.get("name", "Me"),
            properties={"role": role},
        )

        # Add user skills and edges
        user_skills = user_profile.get("skills", [])
        for skill in user_skills[:10]:
            skill_node_id = f"skill_{skill.lower().replace(' ', '_')}"
            G.add_node(
                skill_node_id,
                id=skill_node_id,
                type="skill",
                label=skill,
                properties={},
            )
            G.add_edge(center_node_id, skill_node_id, type="HAS_SKILL")

        # Add user's institution
        if user_profile.get("institution"):
            inst = user_profile["institution"]
            inst_node_id = f"inst_{inst.lower().replace(' ', '_')}"
            G.add_node(inst_node_id, id=inst_node_id, type="institution", label=inst, properties={})
            G.add_edge(center_node_id, inst_node_id, type="AFFILIATED_WITH")

        # Add connected mentors / mentees from mentorship requests
        requests = await mentorship_repo.list_for_user(user_id=user_id, status="accepted", limit=10)
        for req in requests:
            other_id = req["mentor_id"] if req["student_id"] == str(user_id) else req["student_id"]
            other_user = await user_repo.get_by_id(other_id)
            if other_user:
                other_node_id = f"user_{other_id}"
                G.add_node(
                    other_node_id,
                    id=other_node_id,
                    type=other_user.get("role", "alumni"),
                    label=other_user.get("name", "Connection"),
                    properties={"role": other_user.get("role")},
                )
                G.add_edge(center_node_id, other_node_id, type="MENTORED_BY" if role == "student" else "MENTORED")

                # Add shared skills between connections
                other_profile = await profile_repo.get_by_user_id(other_id)
                if other_profile:
                    for skill in other_profile.get("skills", [])[:5]:
                        skill_node_id = f"skill_{skill.lower().replace(' ', '_')}"
                        if G.has_node(skill_node_id):
                            G.add_edge(other_node_id, skill_node_id, type="HAS_SKILL")

        # Extract bounded ego-graph around central user
        ego_subgraph = nx.ego_graph(G, center_node_id, radius=depth)
        
        # Enforce max_nodes bound
        if len(ego_subgraph.nodes) > max_nodes:
            selected_nodes = list(ego_subgraph.nodes)[:max_nodes]
            ego_subgraph = ego_subgraph.subgraph(selected_nodes)

        nodes: List[GraphNode] = []
        for n, data in ego_subgraph.nodes(data=True):
            nodes.append(
                GraphNode(
                    id=str(data.get("id", n)),
                    type=str(data.get("type", "entity")),
                    label=str(data.get("label", n)),
                    properties=data.get("properties", {}),
                )
            )

        edges: List[GraphEdge] = []
        for u, v, data in ego_subgraph.edges(data=True):
            edges.append(
                GraphEdge(
                    source=str(u),
                    target=str(v),
                    type=str(data.get("type", "RELATED_TO")),
                    properties={},
                )
            )

        return GraphResponse(nodes=nodes, edges=edges)

graph_service = GraphService()
