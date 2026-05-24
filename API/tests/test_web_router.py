import pytest



@pytest.mark.anyio
async def test_root_page(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_browse_page(client):
    response = await client.get("/browse")
    assert response.status_code == 200



@pytest.mark.anyio
async def test_search_page_default(client):
    response = await client.get("/search")
    assert response.status_code == 200



@pytest.mark.anyio
async def test_search_page_query(client):
    response = await client.get("/search?query=house&type=meaning")
    assert response.status_code == 200



@pytest.mark.anyio
async def test_lemma_not_found(client):
    response = await client.get("/lemmas/invalid-id")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_search_returns_html(client):
    response = await client.get("/search?query=test")
    assert "text/html" in response.headers["content-type"]