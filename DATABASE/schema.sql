-- =========================================
-- FULL RESET — removes ALL objects from public schema
-- Run with:
-- psql -U postgres -d hebrew_vocab_hub -f reset_db.sql
-- =========================================

-- Drop all tables, views, indexes, sequences, etc.
DROP SCHEMA IF EXISTS public CASCADE;

-- Recreate clean public schema
CREATE SCHEMA public;

-- Restore default permissions
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- ============================================================
-- Hebrew Vocabulary Hub — Normalized Schema
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- ROOTS
-- ------------------------------------------------------------
CREATE TABLE roots (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized  TEXT NOT NULL UNIQUE,
    display     TEXT NOT NULL
);

CREATE INDEX idx_roots_normalized ON roots (normalized);
CREATE INDEX idx_roots_trgm ON roots USING gin (normalized gin_trgm_ops);

-- ------------------------------------------------------------
-- LEMMAS
-- ------------------------------------------------------------
CREATE TABLE lemmas (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hebrew               TEXT NOT NULL,
    hebrew_plain         TEXT,
    transcription        TEXT,
    transcription_plain  TEXT GENERATED ALWAYS AS (
                             lower(
                                 translate(transcription, ''''||chr(8216)||chr(8217)||chr(700)||'`', '     ')
                             )
                         ) STORED,
    part_of_speech       TEXT,
    part_of_speech_plain TEXT,
    meaning              TEXT NOT NULL,
    root_id              UUID REFERENCES roots(id),
    UNIQUE (hebrew, meaning)
);

CREATE INDEX idx_lemmas_hebrew ON lemmas (hebrew);
CREATE INDEX idx_lemmas_hebrew_plain_trgm
    ON lemmas USING gin (hebrew_plain gin_trgm_ops);
CREATE INDEX idx_lemmas_meaning_trgm
    ON lemmas USING gin (meaning gin_trgm_ops);
CREATE INDEX idx_lemmas_transcription_trgm
    ON lemmas USING gin (transcription gin_trgm_ops);
CREATE INDEX idx_lemmas_transcription_plain_trgm
    ON lemmas USING gin (transcription_plain gin_trgm_ops);
CREATE INDEX idx_lemmas_root ON lemmas (root_id);
CREATE INDEX idx_lemmas_pos_trgm ON lemmas USING gin (part_of_speech_plain gin_trgm_ops);

-- ------------------------------------------------------------
-- WORDS
-- ------------------------------------------------------------
CREATE TABLE words (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word    TEXT NOT NULL UNIQUE
);

CREATE INDEX idx_words_word ON words (word);
CREATE INDEX idx_words_trgm ON words USING gin (word gin_trgm_ops);

-- ------------------------------------------------------------
-- WORD ↔ LEMMA
-- ------------------------------------------------------------
CREATE TABLE word_lemmas (
    word_id     UUID NOT NULL REFERENCES words(id)  ON DELETE CASCADE,
    lemma_id    UUID NOT NULL REFERENCES lemmas(id) ON DELETE CASCADE,
    PRIMARY KEY (word_id, lemma_id)
);

-- ------------------------------------------------------------
-- CONJUGATION TABLES
-- ------------------------------------------------------------
CREATE TABLE conj_tables (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma_id    UUID NOT NULL REFERENCES lemmas(id) ON DELETE CASCADE,
    table_index INT NOT NULL DEFAULT 0,
    headers     JSONB NOT NULL DEFAULT '[]'
);

CREATE INDEX idx_conj_tables_lemma ON conj_tables (lemma_id);

-- ------------------------------------------------------------
-- CONJUGATION CELLS
-- ------------------------------------------------------------
CREATE TABLE conj_cells (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id            UUID NOT NULL REFERENCES conj_tables(id) ON DELETE CASCADE,
    labels              TEXT[] NOT NULL DEFAULT '{}',
    cell_index          INT NOT NULL,
    hebrew              TEXT NOT NULL,
    hebrew_plain        TEXT,
    transcription       TEXT,
    transcription_plain TEXT GENERATED ALWAYS AS (
                            lower(
                                translate(transcription, ''''||chr(8216)||chr(8217)||chr(700)||'`', '     ')
                            )
                        ) STORED,
    meaning             TEXT,

    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(meaning, ''))
    ) STORED
);

CREATE INDEX idx_conj_cells_table
    ON conj_cells (table_id);

CREATE INDEX idx_conj_cells_fts
    ON conj_cells USING gin (search_vector);

CREATE INDEX idx_conj_cells_hebrew
    ON conj_cells (hebrew);

CREATE INDEX idx_conj_cells_trgm
    ON conj_cells USING gin (hebrew gin_trgm_ops);
CREATE INDEX idx_conj_cells_hebrew_plain_trgm
    ON conj_cells USING gin (hebrew_plain gin_trgm_ops);
CREATE INDEX idx_conj_cells_transcription_plain_trgm
    ON conj_cells USING gin (transcription_plain gin_trgm_ops);

-- ------------------------------------------------------------
-- SENTENCES
-- ------------------------------------------------------------
CREATE TABLE sentences (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word_id     UUID NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    sentence    TEXT NOT NULL,
    translation TEXT,
    source      TEXT
);

CREATE INDEX idx_sentences_word ON sentences (word_id);

-- ------------------------------------------------------------
-- WORD SOURCES
-- ------------------------------------------------------------
CREATE TABLE word_sources (
    word_id     UUID PRIMARY KEY REFERENCES words(id) ON DELETE CASCADE,
    songs       INT NOT NULL DEFAULT 0,
    news        INT NOT NULL DEFAULT 0,
    youtube     INT NOT NULL DEFAULT 0,
    total       INT NOT NULL DEFAULT 0
);

-- ============================================================
-- VIEWS
-- ============================================================

CREATE VIEW v_cell_search AS
SELECT
    cc.id                    AS cell_id,
    cc.cell_index,
    cc.hebrew                AS cell_hebrew,
    cc.hebrew_plain          AS cell_hebrew_plain,
    cc.transcription         AS cell_transcription,
    cc.transcription_plain   AS cell_transcription_plain,
    cc.meaning               AS cell_meaning,
    cc.labels,
    ct.table_index,

    l.id                     AS lemma_id,
    l.hebrew                 AS lemma_hebrew,
    l.transcription          AS lemma_transcription,
    l.transcription_plain    AS lemma_transcription_plain,
    l.meaning                AS lemma_meaning,
    l.part_of_speech,
    l.part_of_speech_plain,

    r.id                     AS root_id,
    r.display                AS root_display,
    r.normalized             AS root_normalized

FROM conj_cells cc
JOIN conj_tables ct ON ct.id = cc.table_id
JOIN lemmas l       ON l.id  = ct.lemma_id
LEFT JOIN roots r   ON r.id  = l.root_id;


CREATE VIEW v_word_full AS
SELECT
    w.word,

    l.id                     AS lemma_id,
    l.hebrew                 AS lemma_hebrew,
    l.hebrew_plain           AS lemma_hebrew_plain,
    l.transcription          AS lemma_transcription,
    l.transcription_plain    AS lemma_transcription_plain,
    l.part_of_speech,
    l.meaning                AS lemma_meaning,

    r.display                AS root_display,
    r.normalized             AS root_normalized,

    cc.hebrew                AS cell_hebrew,
    cc.hebrew_plain          AS cell_hebrew_plain,
    cc.transcription         AS cell_transcription,
    cc.transcription_plain   AS cell_transcription_plain,
    cc.meaning               AS cell_meaning,
    cc.labels

FROM words w
JOIN word_lemmas wl      ON wl.word_id   = w.id
JOIN lemmas l            ON l.id         = wl.lemma_id
LEFT JOIN roots r        ON r.id         = l.root_id
LEFT JOIN conj_tables ct ON ct.lemma_id  = l.id
LEFT JOIN conj_cells cc  ON cc.table_id  = ct.id
                        AND cc.hebrew_plain = w.word;