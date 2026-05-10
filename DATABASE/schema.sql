-- =========================================
-- EXTENSIONS
-- =========================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =========================================
-- WORDS (identity layer)
-- =========================================
CREATE TABLE words (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  hebrew            text NOT NULL UNIQUE,
  multiple_meanings boolean NOT NULL DEFAULT false,
  sources           jsonb,
  created_at        timestamptz DEFAULT now()
);

-- fast exact + Hebrew search
CREATE INDEX idx_words_hebrew_search
ON words USING gin (to_tsvector('simple', hebrew));


-- =========================================
-- MEANINGS (semantic + search layer)
-- =========================================
CREATE TABLE meanings (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  word_id         uuid NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  meaning_index   int NOT NULL,

  hebrew          text,
  transcription   text,
  root            text,
  part_of_speech  text,
  meaning         text,

  audio_url       text,
  word_url        text,

  -- FULL-TEXT SEARCH VECTOR (Hebrew + English)
  search_vector   tsvector GENERATED ALWAYS AS (
    to_tsvector('simple',
      coalesce(hebrew,'') || ' ' ||
      coalesce(transcription,'') || ' ' ||
      coalesce(root,'') || ' ' ||
      coalesce(part_of_speech,'') || ' ' ||
      coalesce(meaning,'')
    )
  ) STORED,

  UNIQUE (word_id, meaning_index)
);

CREATE INDEX idx_meanings_search
ON meanings USING GIN(search_vector);

CREATE INDEX idx_meanings_word_id ON meanings(word_id);
CREATE INDEX idx_meanings_hebrew ON meanings(hebrew);


-- =========================================
-- INFLECTION TABLES (grammar groups)
-- =========================================
CREATE TABLE inflection_tables (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meaning_id      uuid NOT NULL REFERENCES meanings(id) ON DELETE CASCADE,
  table_index     int NOT NULL,
  headers         jsonb NOT NULL,
  UNIQUE (meaning_id, table_index)
);

CREATE INDEX idx_inflection_tables_meaning_id
ON inflection_tables(meaning_id);


-- =========================================
-- INFLECTION CELLS (actual forms)
-- =========================================
CREATE TABLE inflection_cells (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  table_id        uuid NOT NULL REFERENCES inflection_tables(id) ON DELETE CASCADE,
  labels          text[],
  cell_index      int NOT NULL,

  hebrew          text,
  transcription   text,
  meaning         text
);

CREATE INDEX idx_inflection_cells_table_id
ON inflection_cells(table_id);

CREATE INDEX idx_inflection_cells_hebrew
ON inflection_cells(hebrew);


-- =========================================
-- SENTENCES (examples)
-- =========================================
CREATE TABLE sentences (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  word_id         uuid NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  sentence        text NOT NULL,
  translation     text,
  source          text
);

CREATE INDEX idx_sentences_word_id
ON sentences(word_id);