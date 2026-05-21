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



@pytest.mark.anyio
async def test_search_meaning_basic(client):
    response = await client.get("/api/search?query=peace&type=meaning")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "meaning"
    assert data["total"] > 0
    assert "lemma_hebrew" in data["results"][0]


@pytest.mark.anyio
async def test_search_meaning_no_results(client):
    response = await client.get("/api/search?query=xyznotaword&type=meaning")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


@pytest.mark.anyio
async def test_search_meaning_deep(client):
    response = await client.get("/api/search?query=my friend&type=meaning&deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    results_with_cells = [r for r in data["results"] if r["cell_meaning"] is not None]
    assert len(results_with_cells) > 0



@pytest.mark.anyio
async def test_search_invalid_type(client):
    response = await client.get("/api/search?query=peace&type=invalid")
    assert response.status_code == 400



@pytest.mark.anyio
async def test_search_missing_query(client):
    response = await client.get("/api/search")
    assert response.status_code == 422



@pytest.mark.anyio
async def test_search_word_basic(client):
    response = await client.get("/api/search?query=כתב&type=word")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "word"
    assert data["total"] > 0
    assert "lemma_hebrew" in data["results"][0]



@pytest.mark.anyio
async def test_search_word_no_results(client):
    response = await client.get("/api/search?query=חחחחחחח&type=word")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []



@pytest.mark.anyio
async def test_search_word_deep(client):
    response = await client.get("/api/search?query=כתב&type=word&deep=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    results_with_cells = [r for r in data["results"] if r["cell_meaning"] is not None]
    assert len(results_with_cells) > 0



@pytest.mark.anyio
async def test_search_pos_basic(client):
    response = await client.get("/api/search?query=hifil&type=pos")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "part_of_speech"
    assert data["total"] > 0
    assert "lemma_hebrew" in data["results"][0]



@pytest.mark.anyio
async def test_search_pos_no_results(client):
    response = await client.get("/api/search?query=xyznotapos&type=pos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []



@pytest.mark.anyio
async def test_search_pos_noun(client):
    response = await client.get("/api/search?query=noun&type=pos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    # all results should have part_of_speech containing noun
    for result in data["results"]:
        assert "oun" in result["part_of_speech"].lower()



@pytest.mark.anyio
async def test_search_root_basic(client):
    response = await client.get("/api/search?query=כתב&type=root")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "root"
    assert data["total"] > 0
    assert "lemma_hebrew" in data["results"][0]



@pytest.mark.anyio
async def test_search_root_no_results(client):
    response = await client.get("/api/search?query=בבב&type=pos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []



async def test_search_transcription_exact(client):
    response = await client.get("/api/search?query=katavti&type=transcription")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "transcription"
    assert data["total"] > 0
    assert data["exact"] == True



async def test_search_transcription_fuzzy(client):
    response = await client.get("/api/search?query=catav&type=transcription")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "transcription"
    assert data["total"] > 0
    assert data["exact"] == False



async def test_search_transcription_no_results(client):
    response = await client.get("/api/search?query=zzzzzzzzz&type=transcription")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["exact"] == False



async def test_search_transcription_score(client):
    response = await client.get("/api/search?query=katavti&type=transcription")
    data = response.json()
    exact_results = [r for r in data["results"] if r["score"] == 1.0]
    assert len(exact_results) > 0
