import pytest

@pytest.mark.asyncio
async def test_knowledge_graph_contract(async_client, student_auth):
    headers = student_auth["headers"]
    resp = await async_client.get("/api/v1/graph/me?depth=2&max_nodes=20", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 1
    # Check node structure
    first_node = data["nodes"][0]
    assert "id" in first_node
    assert "type" in first_node
    assert "label" in first_node
    # Bound enforced
    assert len(data["nodes"]) <= 20

@pytest.mark.asyncio
async def test_knowledge_graph_unauthorized(async_client):
    resp = await async_client.get("/api/v1/graph/me")
    assert resp.status_code == 401
