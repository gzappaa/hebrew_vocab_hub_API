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
