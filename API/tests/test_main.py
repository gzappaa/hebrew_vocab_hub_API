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