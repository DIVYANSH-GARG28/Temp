import pytest
from app.services.matching_service import EMBEDDING_MODE, EmbeddingMode

@pytest.mark.asyncio
async def test_mentor_recommendations_contract(async_client, student_auth, alumni_auth):
    headers = student_auth["headers"]
    resp = await async_client.get("/api/v1/mentors/recommendations?limit=10&offset=0", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "algorithm_version" in data
    # algorithm_version now includes embedding mode: 'v1+hash' or 'v1+minilm'
    assert data["algorithm_version"].startswith("v1+")
    assert "total" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "mentor_id" in item
    assert "name" in item
    assert "match_score" in item
    assert 0.0 <= item["match_score"] <= 1.0
    assert "reasons" in item
    assert len(item["reasons"]) > 0
    assert "code" in item["reasons"][0]
    assert "label" in item["reasons"][0]
    assert item["can_request"] is True

@pytest.mark.asyncio
async def test_mentor_recommendations_filter_and_pagination(async_client, student_auth, alumni_auth):
    headers = student_auth["headers"]
    resp = await async_client.get(
        "/api/v1/mentors/recommendations?skill=FastAPI&career_goal=Backend%20Engineering&limit=5&offset=0",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) >= 1
    assert data["items"][0]["mentor_id"] == alumni_auth["user"]["id"]

@pytest.mark.asyncio
async def test_embedding_mode_is_explicitly_reported(async_client, student_auth, alumni_auth):
    """Verify EMBEDDING_MODE is set and the API response discloses it."""
    # EMBEDDING_MODE must be one of the known modes — never an unknown string
    assert EMBEDDING_MODE in (EmbeddingMode.MINILM, EmbeddingMode.HASH)

    headers = student_auth["headers"]
    resp = await async_client.get("/api/v1/mentors/recommendations?limit=1", headers=headers)
    assert resp.status_code == 200
    version = resp.json()["algorithm_version"]

    # The reported mode in the API response must match the runtime mode
    expected_suffix = EMBEDDING_MODE.value
    assert version == f"v1+{expected_suffix}", (
        f"API reported '{version}' but EMBEDDING_MODE is '{EMBEDDING_MODE.value}'. "
        "Mismatch indicates the service is not disclosing the active embedding mode."
    )

@pytest.mark.asyncio
async def test_hash_fallback_produces_64_dim_vector():
    """Fallback encoder must produce exactly 64 dimensions — not 384."""
    from app.services.matching_service import _embed_text_fallback
    vec = _embed_text_fallback("machine learning python backend engineering")
    assert len(vec) == 64, f"Expected 64-dim hash vector, got {len(vec)}"
    # Vector must be unit-normalised
    import math
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-6 or norm == 0.0, f"Hash vector not unit-normalised: norm={norm}"

@pytest.mark.asyncio
async def test_minilm_produces_384_dim_vector_when_installed():
    """When sentence-transformers is installed, encode_text must return 384-dim vectors."""
    from app.services.matching_service import _sentence_model, encode_text, EMBEDDING_MODE, EmbeddingMode
    if EMBEDDING_MODE != EmbeddingMode.MINILM:
        pytest.skip("sentence-transformers not installed; skipping MiniLM dimension test")
    vec = encode_text("machine learning python")
    assert len(vec) == 384, (
        f"MiniLM must produce 384-dim vectors, got {len(vec)}. "
        "If fallback is accidentally active, check EMBEDDING_MODE."
    )
