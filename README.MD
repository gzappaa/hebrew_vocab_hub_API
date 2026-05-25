# hebrew_vocab_hub

A Hebrew vocabulary platform built on top of a scraped and assembled dataset of ~13,000 Hebrew lemmas (150k unique words). It exposes the data through a **FastAPI** REST + web interface backed by a normalized **PostgreSQL** schema, fully containerized with Docker Compose.

> The dataset itself (`vocab_dataset.json`) is produced by a separate scraping pipeline — https://github.com/gzappaa/hebrew_vocab_hub

---

## What it includes

- **`DATABASE/`** — PostgreSQL schema, data importer, and database tests
- **`API/`** — Async FastAPI app with a JSON REST API and an HTML web UI
- **`docker-compose.yml`** — One-command deployment: spins up Postgres, imports the dataset, and starts the API

---

## Quick start

### 1. Clone and set up

```bash
git clone https://github.com/gzappaa/hebrew_vocab_hub_API
cd hebrew_vocab_hub
python DATABASE/setup_data.py
```

`setup_data.py` does two things:
- Renames `.env.example` → `.env` and `API/.env.prod.example` → `API/.env.prod` (if they don't exist yet)
- Downloads `vocab_dataset.json` from Google Drive into `DATABASE/`

### 2. Configure environment

Edit `.env` at the project root:

```env
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=password
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DBNAME=hebrew_vocab_hub
```

Edit `API/.env.prod`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/hebrew_vocab_hub
ENV=prod
DEBUG=false
```

### 3. Run

```bash
docker compose up --build
```

This starts three services in order:

| Service | What it does |
|---------|-------------|
| `db` | PostgreSQL 16, initialized from `DATABASE/schema.sql` |
| `importer` | Reads `vocab_dataset.json` and imports all words, lemmas, conjugations, sentences, and sources |
| `api` | FastAPI app served on `http://localhost:8000` |

---

## API

Base URL: `http://localhost:8000`

### `GET /api/browse`

Paginated list of all lemmas, sorted alphabetically.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int ≥ 1 | 1 | Page number |
| `page_size` | int 1–100 | 40 | Results per page |

```
GET /api/browse?page=2&page_size=20
```

```json
{
  "total": 13000,
  "page": 2,
  "page_size": 20,
  "total_pages": 650,
  "results": [
    {
      "id": "uuid",
      "lemma_url": "/lemmas/uuid",
      "hebrew": "אָב",
      "transcription": "av",
      "part_of_speech": "Noun - masculine",
      "meaning": "father",
      "root_display": "א - ב"
    }
  ]
}
```

---

### `GET /api/search`

Search the vocabulary by several dimensions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search term |
| `type` | string | `meaning` | One of `meaning`, `word`, `pos`, `root`, `transcription` |
| `limit` | int | 5000 | Max results |
| `deep` | bool | `false` | Also search inside conjugation cells |

**Search types:**

| Type | Searches | Match |
|------|----------|-------|
| `meaning` | Lemma meanings (+ cell meanings if `deep=true`) | `ILIKE %query%` |
| `word` | Hebrew word forms (inflected) | Exact, or trigram if `deep=true` |
| `pos` | Part of speech | `ILIKE %query%` |
| `root` | Normalized root | `ILIKE %query%` |
| `transcription` | Latin transcription | Exact first, then trigram fuzzy fallback (up to 5) |

```
GET /api/search?query=peace&type=meaning
GET /api/search?query=כתב&type=word&deep=true
GET /api/search?query=katavti&type=transcription
```

```json
{
  "query": "peace",
  "type": "meaning",
  "total": 3,
  "exact": false,
  "results": [
    {
      "lemma_id": "uuid",
      "lemma_url": "/lemmas/uuid",
      "lemma_hebrew": "שָׁלוֹם",
      "lemma_meaning": "peace, hello, goodbye",
      "lemma_transcription": "shalom",
      "part_of_speech": "Noun - masculine",
      "root": { "display": "ש - ל - ם", "normalized": "שלם" },
      "cell_hebrew": null,
      "cell_transcription": null,
      "cell_meaning": null,
      "score": null
    }
  ]
}
```

The `exact` field is only meaningful for `transcription` searches — `true` means at least one result was a 1.0 similarity match.

---

### `GET /api/lemmas/{lemma_id}`

Full detail for a single lemma by UUID.

```
GET /api/lemmas/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

```json
{
  "id": "uuid",
  "hebrew": "כָּתַב",
  "transcription": "katav",
  "part_of_speech": "Verb - pa'al",
  "meaning": "to write",
  "root": { "display": "כ - ת - ב", "normalized": "כתב" },
  "conj_tables": [
    {
      "table_index": 0,
      "headers": ["Past", "masculine", "feminine"],
      "cells": [
        {
          "row_index": 0,
          "cell_index": 0,
          "labels": ["1st person", "singular"],
          "hebrew": "כָּתַבְתִּי",
          "transcription": "katavti",
          "meaning": "I wrote"
        }
      ]
    }
  ],
  "sentences": [
    {
      "sentence": "הוא כתב מכתב.",
      "translation": "He wrote a letter.",
      "source": "tatoeba",
      "word": "כתב"
    }
  ],
  "sources": {
    "songs": 12,
    "news": 34,
    "youtube": 5,
    "total": 51
  }
}
```

---

### `GET /ping-db`

Health check — confirms the API can reach the database.

```json
{ "status": "ok", "db": "connected" }
```

---

### Error responses

All `/api/` errors return JSON. Web routes return an HTML error page.

| Status | Meaning |
|--------|---------|
| 400 | Invalid search `type` |
| 404 | Lemma not found, or page out of range |
| 422 | Missing or invalid query parameters |

---

## Web UI

The same data is accessible through rendered HTML pages:

| Route | Description |
|-------|-------------|
| `/` | Home page |
| `/browse?page=1&page_size=20` | Paginated word list |
| `/search?query=...&type=...&deep=...` | Search results page |
| `/lemmas/{lemma_id}` | Full lemma detail with conjugation tables |

Swagger docs are available at `/docs` when `DEBUG=true`.

---

## Database schema

```
roots
  id, normalized, display

lemmas
  id, hebrew, hebrew_plain, transcription, transcription_plain (generated),
  part_of_speech, part_of_speech_plain, meaning, root_id → roots

words
  id, word

word_lemmas
  word_id → words, lemma_id → lemmas          (many-to-many)

conj_tables
  id, lemma_id → lemmas, table_index, headers (JSONB)

conj_cells
  id, table_id → conj_tables, labels (TEXT[]),
  row_index, cell_index, hebrew, hebrew_plain,
  transcription, transcription_plain (generated),
  meaning, search_vector (TSVECTOR, generated)

sentences
  id, word_id → words, sentence, translation, source

word_sources
  word_id → words, songs, news, youtube, total
```

**Extensions used:** `pg_trgm` (fuzzy search), `unaccent`, `pgcrypto` (UUID generation).

**Views:**
- `v_cell_search` — flat join of lemma + root + conjugation cells, used by all search queries
- `v_word_full` — word-centric join that matches a surface form to its lemma and the cell whose `hebrew_plain` equals the word

---

## Project structure

```
hebrew_vocab_hub/
├── docker-compose.yml
├── .env                        # root env (Postgres credentials)
├── .env.example
│
├── DATABASE/
│   ├── schema.sql              # Full schema: tables, indexes, views
│   ├── import_vocab.py         # Loads vocab_dataset.json → Postgres
│   ├── init_db.py              # Called by Docker on first start
│   ├── setup_data.py           # Downloads dataset, sets up env files
│   └── tests/
│       ├── conftest.py
│       ├── test_integrity.py
│       ├── test_search.py
│       ├── test_edgecases.py
│       └── test_perfomance.py
│
└── API/
    ├── Dockerfile
    ├── requirements.txt
    ├── config.py
    ├── logging_conf.py
    ├── pytest.ini
    ├── .env.prod.example       <- will change to .env.prod
    ├── static/
    ├── app/
    │   ├── main.py             # FastAPI app, middleware, health check
    │   ├── api_router.py       # /api/* endpoints
    │   ├── web_router.py       # HTML page routes
    │   ├── queries.py          # All async SQLAlchemy queries
    │   ├── schemas.py          # Pydantic response models
    │   ├── database.py         # Async engine + session factory
    │   ├── errors_handler.py   # JSON errors for /api/, HTML for web
    │   └── templates/
    │       ├── base.html
    │       ├── index.html
    │       ├── browse.html
    │       ├── search.html
    │       ├── lemma.html
    │       └── error.html
    └── tests/
        ├── conftest.py
        ├── test_api_router.py
        ├── test_web_router.py
        ├── test_main.py
        └── test_errors_handler.py
```

---

## Running tests

**API tests** (requires a running test database — see `API/pytest.ini` and `tests/conftest.py`):

```bash
cd API
pytest
```

**Database tests:**

```bash
cd DATABASE
pytest
```

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| API framework | FastAPI (async) |
| ORM / queries | SQLAlchemy async + raw SQL |
| Validation | Pydantic v2 |
| Database | PostgreSQL 16 |
| Search | `pg_trgm` trigram similarity |
| Containerization | Docker Compose |
| Testing | pytest + anyio |

---

## License

MIT