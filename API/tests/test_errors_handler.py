import pytest


# --------------------------------------------------
# API → HTTPException returns JSON
# --------------------------------------------------

@pytest.mark.anyio
async def test_api_404_returns_json(client):

    response = await client.get("/api/route-that-does-not-exist")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], str)


# --------------------------------------------------
# WEB → HTTPException returns HTML
# --------------------------------------------------

@pytest.mark.anyio
async def test_web_404_returns_html(client):

    response = await client.get("/lemmas/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404

    assert "text/html" in response.headers["content-type"]


# --------------------------------------------------
# API → validation error returns JSON
# --------------------------------------------------

@pytest.mark.anyio
async def test_api_validation_error_returns_json(client):

    response = await client.get("/api/lemmas/invalid-id")

    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], list)


# --------------------------------------------------
# WEB → validation error returns HTML
# --------------------------------------------------

@pytest.mark.anyio
async def test_web_validation_error_returns_html(client):

    response = await client.get("/lemmas/invalid-id")

    assert response.status_code == 422

    assert "text/html" in response.headers["content-type"]


# --------------------------------------------------
# API validation structure
# --------------------------------------------------

@pytest.mark.anyio
async def test_api_validation_error_has_expected_structure(client):

    response = await client.get("/api/lemmas/invalid-id")

    data = response.json()

    error = data["detail"][0]

    assert "type" in error
    assert "loc" in error
    assert "msg" in error


# --------------------------------------------------
# HTML error page contains status code
# --------------------------------------------------

@pytest.mark.anyio
async def test_web_error_page_contains_status_code(client):

    response = await client.get("/lemmas/invalid-id")

    content = response.text

    assert "422" in content


# --------------------------------------------------
# HTML error page contains message
# --------------------------------------------------

@pytest.mark.anyio
async def test_web_error_page_contains_error_message(client):

    response = await client.get("/lemmas/invalid-id")

    content = response.text.lower()

    assert "uuid" in content or "valid" in content


# --------------------------------------------------
# API content type is json
# --------------------------------------------------

@pytest.mark.anyio
async def test_api_error_content_type(client):

    response = await client.get("/api/lemmas/invalid-id")

    assert response.headers["content-type"].startswith(
        "application/json"
    )


# --------------------------------------------------
# WEB content type is html
# --------------------------------------------------

@pytest.mark.anyio
async def test_web_error_content_type(client):

    response = await client.get("/lemmas/invalid-id")

    assert response.headers["content-type"].startswith(
        "text/html"
    )