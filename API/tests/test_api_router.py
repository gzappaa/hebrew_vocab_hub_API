import pytest


# ==================================================
# BROWSE
# ==================================================

@pytest.mark.anyio
async def test_browse_page_ok(client):

    response = await client.get("/api/browse?page=2")

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["results"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "page,expected_status",
    [
        pytest.param(0, 422, id="page_less_than_1"),
        pytest.param(9999, 404, id="page_does_not_exist"),
    ]
)
async def test_browse_invalid_pages(
    client,
    page,
    expected_status,
):
    response = await client.get(f"/api/browse?page={page}")

    assert response.status_code == expected_status


# ==================================================
# SEARCH — BASIC
# ==================================================

@pytest.mark.anyio
@pytest.mark.parametrize(
    "query,search_type,expected_type",
    [
        pytest.param("peace", "meaning", "meaning", id="meaning"),
        pytest.param("כתב", "word", "word", id="word"),
        pytest.param("hifil", "pos", "part_of_speech", id="pos"),
        pytest.param("כתב", "root", "root", id="root"),
    ]
)
async def test_search_basic(
    client,
    query,
    search_type,
    expected_type,
):
    response = await client.get(
        f"/api/search?query={query}&type={search_type}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == expected_type
    assert data["total"] > 0
    assert "lemma_hebrew" in data["results"][0]


# ==================================================
# SEARCH — NO RESULTS
# ==================================================

@pytest.mark.anyio
@pytest.mark.parametrize(
    "query,search_type",
    [
        pytest.param("xyznotaword", "meaning", id="meaning"),
        pytest.param("חחחחחחח", "word", id="word"),
        pytest.param("xyznotapos", "pos", id="pos"),
        pytest.param("בבב", "root", id="root"),
        pytest.param("zzzzzzzzz", "transcription", id="transcription"),
    ]
)
async def test_search_no_results(
    client,
    query,
    search_type,
):
    response = await client.get(
        f"/api/search?query={query}&type={search_type}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 0
    assert data["results"] == []


# ==================================================
# SEARCH — DEEP
# ==================================================

@pytest.mark.anyio
@pytest.mark.parametrize(
    "query,search_type",
    [
        pytest.param("my friend", "meaning", id="meaning"),
        pytest.param("כתב", "word", id="word"),
    ]
)
async def test_search_deep(
    client,
    query,
    search_type,
):
    response = await client.get(
        f"/api/search?query={query}&type={search_type}&deep=true"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] > 0

    results_with_cells = [
        r for r in data["results"]
        if r["cell_meaning"] is not None
    ]

    assert results_with_cells


# ==================================================
# SEARCH — VALIDATION
# ==================================================

@pytest.mark.anyio
async def test_search_invalid_type(client):

    response = await client.get(
        "/api/search?query=peace&type=invalid"
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_search_missing_query(client):

    response = await client.get("/api/search")

    assert response.status_code == 422


# ==================================================
# SEARCH — POS SPECIAL CASE
# ==================================================

@pytest.mark.anyio
async def test_search_pos_noun(client):

    response = await client.get(
        "/api/search?query=noun&type=pos"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] > 0

    for result in data["results"]:
        assert "noun" in result["part_of_speech"].lower()


# ==================================================
# SEARCH — TRANSCRIPTION
# ==================================================

@pytest.mark.anyio
async def test_search_transcription_exact(client):

    response = await client.get(
        "/api/search?query=katavti&type=transcription"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "transcription"
    assert data["total"] > 0
    assert data["exact"] is True


@pytest.mark.anyio
async def test_search_transcription_fuzzy(client):

    response = await client.get(
        "/api/search?query=catav&type=transcription"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "transcription"
    assert data["total"] > 0
    assert data["exact"] is False


@pytest.mark.anyio
async def test_search_transcription_score(client):

    response = await client.get(
        "/api/search?query=katavti&type=transcription"
    )

    data = response.json()

    exact_results = [
        r for r in data["results"]
        if r["score"] == 1.0
    ]

    assert exact_results


# ==================================================
# LEMMA DETAIL
# ==================================================

@pytest.mark.anyio
async def test_get_lemma_detail_ok(client):

    browse = await client.get("/api/browse?page=1")

    browse_data = browse.json()

    lemma_id = browse_data["results"][0]["id"]

    res = await client.get(f"/api/lemmas/{lemma_id}")

    assert res.status_code == 200

    data = res.json()

    # core fields
    assert data["id"] == lemma_id
    assert "hebrew" in data
    assert isinstance(data["hebrew"], str)

    # sentences
    assert "sentences" in data
    assert isinstance(data["sentences"], list)

    if data["sentences"]:
        s = data["sentences"][0]

        assert "sentence" in s
        assert "word" in s

        assert isinstance(s["sentence"], str)
        assert isinstance(s["word"], str)

    # sources
    assert "sources" in data

    if data["sources"] is not None:

        assert "songs" in data["sources"]
        assert "news" in data["sources"]
        assert "youtube" in data["sources"]
        assert "total" in data["sources"]

        assert data["sources"]["total"] >= 0


@pytest.mark.anyio
async def test_get_lemma_detail_not_found(client):

    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(
        f"/api/lemmas/{fake_id}"
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_lemma_detail_invalid_uuid(client):

    response = await client.get("/api/lemmas/abc")

    assert response.status_code == 422