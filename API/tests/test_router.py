import pytest



@pytest.mark.anyio
async def test_browse_page2(client):
    response = await client.get("/api/lemmas?page=2")
    assert response.status_code == 200
    assert response.json()["page"] == 2


@pytest.mark.anyio
async def test_browse_invalid_page_greater_than_total(client):
    response = await client.get("/api/lemmas?page=9999")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]

@pytest.mark.anyio
async def test_browse_invalid_page_less_than_1(client):
    response = await client.get("/api/lemmas?page=0")
    assert response.status_code == 422


async def test_search_meaning_basic(client):
    response = await client.get("/api/search?query=peace")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "meaning"
    assert data["total"] > 0
    assert "lemma_hebrew" in data["results"][0]

async def test_search_meaning_no_results(client):
    response = await client.get("/api/search?query=xyznotaword")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []

async def test_search_meaning_deep(client):
    response = await client.get("/api/search?query=my friend&deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    # deep search should return cell data
    results_with_cells = [r for r in data["results"] if r["cell_meaning"] is not None]
    assert len(results_with_cells) > 0

async def test_search_invalid_type(client):
    response = await client.get("/api/search?query=peace&type=invalid")
    assert response.status_code == 400

async def test_search_missing_query(client):
    response = await client.get("/api/search")
    assert response.status_code == 422  # FastAPI validation error

