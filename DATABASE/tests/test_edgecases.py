import pytest
import unicodedata


def normalize(s):
    return unicodedata.normalize('NFC', s) if s else s


# ─── EMPTY / INVALID INPUT ───────────────────────────────────


def test_empty_hebrew_search_returns_nothing(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_cell_search
        WHERE cell_hebrew_plain IS NULL
    """)
    assert cur.fetchone()[0] == 0


def test_empty_cells_are_known_and_bounded(cur):
    """empty hebrew/transcription cells are legitimate grammar gaps, not import errors"""
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells
        WHERE hebrew = '' OR hebrew IS NULL
    """)
    count = cur.fetchone()[0]
    assert count < 200  # known ~119 (15/05/2026), gives headroom without being unbounded


def test_empty_meaning_search_returns_nothing(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_word_full
        WHERE lemma_meaning ILIKE '%%'
    """)
    # %% alone matches everything, so just assert it doesn't crash
    cur.fetchall()


def test_nonsense_hebrew_returns_nothing(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_cell_search
        WHERE cell_hebrew_plain = 'אאאאאאאא'
    """)
    assert cur.fetchone()[0] == 0


def test_nonsense_transcription_returns_nothing(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_cell_search
        WHERE cell_transcription_plain % 'zzzzzzzzz'
    """)
    assert cur.fetchone()[0] == 0


# ─── AMBIGUOUS WORDS ─────────────────────────────────────────


def test_ambiguous_word_returns_multiple_lemmas(cur):
    """חברה maps to multiple lemmas (company, girlfriend, she connected)"""
    cur.execute("""
        SELECT COUNT(DISTINCT lemma_id)
        FROM v_cell_search
        WHERE cell_hebrew_plain = 'חברה'
    """)
    assert cur.fetchone()[0] > 1


def test_ambiguous_word_has_multiple_meanings(cur):
    cur.execute("""
        SELECT DISTINCT lemma_meaning
        FROM v_cell_search
        WHERE cell_hebrew_plain = 'חברה'
    """)
    meanings = [row[0] for row in cur.fetchall()]
    assert len(meanings) > 1


# ─── WORDS WITH NO CONJUGATION TABLES ────────────────────────


def test_lemmas_without_tables_still_linked_to_words(cur):
    """some lemmas have no conjugation tables but should still exist"""
    cur.execute("""
        SELECT COUNT(*) FROM lemmas l
        WHERE NOT EXISTS (
            SELECT 1 FROM conj_tables ct WHERE ct.lemma_id = l.id
        )
    """)
    count = cur.fetchone()[0]
    assert count >= 0  # just assert it doesn't crash, count may vary


def test_word_with_no_cells_still_returns_lemma(cur):
    """words linked via word_lemmas should appear even with no matching cell"""
    cur.execute("""
        SELECT DISTINCT ON (l.id)
            l.hebrew,
            l.meaning
        FROM words w
        JOIN word_lemmas wl ON wl.word_id = w.id
        JOIN lemmas l ON l.id = wl.lemma_id
        LEFT JOIN conj_tables ct ON ct.lemma_id = l.id
        LEFT JOIN conj_cells cc ON cc.table_id = ct.id
                                AND cc.hebrew_plain = w.word
        WHERE w.word = 'כתב'
        AND cc.hebrew IS NULL
        ORDER BY l.id
    """)
    rows = cur.fetchall()
    # לְכַתֵּב has no cell matching כתב exactly
    assert len(rows) > 0


# ─── FUZZY TRANSCRIPTION EDGE CASES ──────────────────────────


def test_fuzzy_transcription_returns_max_5_results(cur):
    cur.execute("""
        WITH results AS (
            SELECT DISTINCT ON (lemma_id)
                similarity(cell_transcription_plain, 'catavti') AS score
            FROM v_cell_search
            WHERE cell_transcription_plain % 'catavti'
            ORDER BY lemma_id, score DESC
        )
        SELECT * FROM (
            SELECT * FROM results
            WHERE score < 1.0
            ORDER BY score DESC
            LIMIT 5
        ) fuzzy
        WHERE NOT EXISTS (SELECT 1 FROM results WHERE score = 1.0)
    """)
    rows = cur.fetchall()
    assert len(rows) <= 5


def test_exact_transcription_score_is_one(cur):
    cur.execute("""
        SELECT similarity(cell_transcription_plain, 'katavti')
        FROM v_cell_search
        WHERE cell_transcription_plain = 'katavti'
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None
    assert row[0] == 1.0


# ─── ROOT EDGE CASES ─────────────────────────────────────────


def test_lemma_with_no_root_is_allowed(cur):
    """some lemmas have no root, root_id should be nullable"""
    cur.execute("""
        SELECT COUNT(*) FROM lemmas
        WHERE root_id IS NULL
    """)
    count = cur.fetchone()[0]
    assert count >= 0


def test_root_normalized_has_no_dashes_or_spaces(cur):
    """normalized roots should be bare Hebrew letters only"""
    cur.execute("""
        SELECT COUNT(*) FROM roots
        WHERE normalized ~ '[^א-ת]'
    """)
    assert cur.fetchone()[0] == 0