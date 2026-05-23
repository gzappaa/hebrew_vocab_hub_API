"""
import_vocab.py
--------------
Reads vocab_dataset.json and imports into hebrew_vocab_hub PostgreSQL database.

Usage:
    pip install psycopg2-binary python-dotenv
    python import_vocab.py

Adjust .env before running.
"""

import os
import re
import json
import uuid
import psycopg2

from dotenv import load_dotenv
from pathlib import Path
from psycopg2.extras import execute_values


# ─── PATHS ───────────────────────────────────────────────────

JSON_PATH = Path(__file__).resolve().parent / "vocab_dataset.json"


# ─── LOAD ENV ────────────────────────────────────────────────

load_dotenv()

import sys

if "--prod" not in sys.argv and "--test" not in sys.argv:
    print("Error: you must specify --prod or --test")
    sys.exit(1)

test_mode = "--test" in sys.argv

DB_CONFIG = {
    "host":     os.getenv("POSTGRESQL_HOST"),
    "port":     os.getenv("POSTGRESQL_PORT"),
    "dbname":   os.getenv("TEST_POSTGRESQL_DBNAME" if test_mode else "POSTGRESQL_DBNAME"),
    "user":     os.getenv("POSTGRESQL_USER"),
    "password": os.getenv("POSTGRESQL_PASSWORD"),
}

# ─── HELPERS ─────────────────────────────────────────────────

def normalize_root(root_str: str) -> str:
    """
    "ה - ל - ך" → "הלך"
    Removes everything except Hebrew letters.
    """
    if not root_str or root_str.strip() == "-":
        return ""

    return re.sub(r"[^א-ת]", "", root_str)


def new_id() -> str:
    return str(uuid.uuid4())


def normalize_pos(p: str | None) -> str | None:
    if not p:
        return p
    return (
        p.replace("'", "")
         .replace("\u2019", "")
         .replace("-", " ")
         .strip()
         .lower()
    )


def normalize_transcription(t: str | None) -> str | None:
    if not t:
        return t
    return (
        t.replace("'",  "")
         .replace("\u2019", "")
         .replace("\u2018", "")
         .replace("`",  "")
         .replace("ʼ",  "")
         .replace("!",  "")
         .replace("?",  "")
    )

def strip_nikud(h: str | None) -> str | None:
    if not h:
        return h
    h = re.sub(r'[\u05B0-\u05C7]', '', h)  # nikud
    h = re.sub(r'[!?.,;:״׃]', '', h)        # punctuation
        # Strip invisible Unicode formatting/directional characters
    h = re.sub(r'[\u200B-\u200F\u202A-\u202E\uFEFF]', '', h)
    return h
    return h


# ─── IMPORTER ────────────────────────────────────────────────

def import_vocab(conn, data: list[dict]):
    cur = conn.cursor()

    root_cache: dict[str, str] = {}
    lemma_cache: dict[tuple, str] = {}

    total = len(data)

    for i, entry in enumerate(data, 1):

        surface_word = entry["word"]

        if i % 500 == 0:
            print(f"  {i}/{total} — {surface_word}")
            conn.commit()

        # ── WORD ─────────────────────────────────────────────

        cur.execute(
            """
            INSERT INTO words (id, word)
            VALUES (%s, %s)
            ON CONFLICT (word)
            DO UPDATE SET word = EXCLUDED.word
            RETURNING id
            """,
            (new_id(), surface_word),
        )

        word_id = cur.fetchone()[0]

        # ── SENTENCES ───────────────────────────────────────

        for s in entry.get("sentences", []):

            cur.execute(
                """
                INSERT INTO sentences
                    (id, word_id, sentence, translation, source)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    new_id(),
                    word_id,
                    s.get("sentence"),
                    s.get("translation"),
                    s.get("source"),
                ),
            )

        # ── SOURCES ─────────────────────────────────────────

        src = entry.get("sources", {})

        if src:
            cur.execute(
                """
                INSERT INTO word_sources
                    (word_id, songs, news, youtube, total)
                VALUES (%s, %s, %s, %s, %s)

                ON CONFLICT (word_id)
                DO UPDATE SET
                    songs   = EXCLUDED.songs,
                    news    = EXCLUDED.news,
                    youtube = EXCLUDED.youtube,
                    total   = EXCLUDED.total
                """,
                (
                    word_id,
                    src.get("songs", 0),
                    src.get("news", 0),
                    src.get("youtube", 0),
                    src.get("total", 0),
                ),
            )

        # ── MEANINGS / LEMMAS ──────────────────────────────

        for meaning_obj in entry.get("meanings", []):

            lemma_hebrew = meaning_obj.get("hebrew", "")
            lemma_meaning = meaning_obj.get("meaning", "")

            lemma_key = (lemma_hebrew, lemma_meaning)

            if lemma_key not in lemma_cache:

                # ── ROOT ───────────────────────────────────

                root_id = None

                raw_root = meaning_obj.get("root", "")
                norm_root = normalize_root(raw_root)

                if norm_root:

                    if norm_root not in root_cache:

                        cur.execute(
                            """
                            INSERT INTO roots
                                (id, normalized, display)
                            VALUES (%s, %s, %s)

                            ON CONFLICT (normalized)
                            DO UPDATE SET
                                display = EXCLUDED.display

                            RETURNING id
                            """,
                            (
                                new_id(),
                                norm_root,
                                raw_root,
                            ),
                        )

                        root_cache[norm_root] = cur.fetchone()[0]

                    root_id = root_cache[norm_root]

                # ── LEMMA ─────────────────────────────────

                cur.execute(
                    """
                    INSERT INTO lemmas
                        (
                            id,
                            hebrew,
                            hebrew_plain,
                            transcription,
                            part_of_speech,
                            part_of_speech_plain,
                            meaning,
                            root_id
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

                    ON CONFLICT (hebrew, meaning)
                    DO UPDATE SET
                        hebrew_plain = EXCLUDED.hebrew_plain,
                        transcription = EXCLUDED.transcription,
                        part_of_speech = EXCLUDED.part_of_speech,
                        part_of_speech_plain = EXCLUDED.part_of_speech_plain,
                        root_id = EXCLUDED.root_id

                    RETURNING id
                    """,
                    (
                        new_id(),
                        lemma_hebrew,
                        strip_nikud(lemma_hebrew),
                        normalize_transcription(meaning_obj.get("transcription")),
                        meaning_obj.get("part_of_speech"),
                        normalize_pos(meaning_obj.get("part_of_speech")),
                        lemma_meaning,
                        root_id,
                    ),
                )

                lemma_cache[lemma_key] = cur.fetchone()[0]

                # ── CONJUGATION TABLES ────────────────────

                lemma_id = lemma_cache[lemma_key]

                for t_idx, table in enumerate(meaning_obj.get("tables", [])):

                    table_id = new_id()

                    cur.execute(
                        """
                        INSERT INTO conj_tables
                            (id, lemma_id, table_index, headers)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            table_id,
                            lemma_id,
                            t_idx,
                            json.dumps(table.get("headers", [])),
                        ),
                    )

                    cell_rows = []

                    for r_idx, row in enumerate(table.get("rows", [])):

                        labels = row.get("labels", [])

                        for c_idx, cell in enumerate(row.get("cells", [])):

                            cell_rows.append(
                                (
                                    new_id(),
                                    table_id,
                                    labels,
                                    r_idx,      # row_index
                                    c_idx,      # cell_index
                                    cell.get("hebrew", ""),
                                    strip_nikud(cell.get("hebrew", "")),
                                    normalize_transcription(cell.get("transcription")),
                                    cell.get("meaning"),
                                )
                            )

                    if cell_rows:

                        execute_values(
                            cur,
                            """
                            INSERT INTO conj_cells
                                (
                                    id,
                                    table_id,
                                    labels,
                                    row_index,
                                    cell_index,
                                    hebrew,
                                    hebrew_plain,
                                    transcription,
                                    meaning
                                )
                            VALUES %s
                            """,
                            cell_rows,
                        )

            # ── WORD ↔ LEMMA ──────────────────────────────

            lemma_id = lemma_cache[lemma_key]

            cur.execute(
                """
                INSERT INTO word_lemmas
                    (word_id, lemma_id)
                VALUES (%s, %s)

                ON CONFLICT DO NOTHING
                """,
                (
                    word_id,
                    lemma_id,
                ),
            )

    conn.commit()
    cur.close()


# ─── ENTRY POINT ─────────────────────────────────────────────

if __name__ == "__main__":

    print(
        f"Connecting to "
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']} ..."
    )

    conn = psycopg2.connect(**DB_CONFIG)

    print(f"Loading {JSON_PATH} ...")

    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Importing {len(data)} words ...")

    import_vocab(conn, data)

    conn.close()

    print("Done ✓")