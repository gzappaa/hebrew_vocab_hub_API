import pytest




@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_ping_db(client):
    response = await client.get("/ping-db")
    assert response.status_code == 200
    assert response.json()["db"] == "connected"

@pytest.mark.anyio
async def test_lemmas(client):
    response = await client.get("/test-lemmas")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "hebrew" in data[0]
    assert "meaning" in data[0]