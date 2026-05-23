import pytest



@pytest.mark.anyio
async def test_root_page(client):
    resp = await client.get("/")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_browse_page(client):
    resp = await client.get("/browse")
    assert resp.status_code == 200



@pytest.mark.anyio
async def test_search_page_default(client):
    resp = await client.get("/search")
    assert resp.status_code == 200



@pytest.mark.anyio
async def test_search_page_query(client):
    resp = await client.get("/search?query=house&type=meaning")
    assert resp.status_code == 200



@pytest.mark.anyio
async def test_lemma_not_found(client):
    resp = await client.get("/lemmas/invalid-id")
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_search_returns_html(client):
    resp = await client.get("/search?query=test")
    assert "text/html" in resp.headers["content-type"]