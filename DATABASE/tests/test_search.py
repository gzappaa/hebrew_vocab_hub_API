import pytest


# ─── HEBREW SEARCH ───────────────────────────────────────────


def test_search_by_hebrew_returns_correct_count(cur):
    """כתב should return exactly 4 distinct lemmas"""
    cur.execute("""
        SELECT DISTINCT ON (lemma_id)
            lemma_hebrew,
            lemma_meaning,
            part_of_speech,
            cell_hebrew,
            cell_transcription,
            cell_meaning,
            labels
        FROM v_cell_search
        WHERE cell_hebrew_plain = 'כתב'
        ORDER BY lemma_id, cell_id
    """)
    assert len(cur.fetchall()) == 4


import unicodedata

def test_search_by_hebrew_returns_correct_lemmas(cur):
    cur.execute("""
        SELECT DISTINCT lemma_hebrew
        FROM v_cell_search
        WHERE cell_hebrew_plain = 'כתב'
    """)
    lemmas = {unicodedata.normalize('NFC', row[0]) for row in cur.fetchall()}
    assert unicodedata.normalize('NFC', 'לִכְתּוֹב') in lemmas
    assert unicodedata.normalize('NFC', 'כְּתָב') in lemmas
    assert unicodedata.normalize('NFC', 'כַּתָּב') in lemmas
    assert unicodedata.normalize('NFC', 'לְכַתֵּב') in lemmas


def test_search_by_hebrew_no_results(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_cell_search
        WHERE cell_hebrew_plain = 'קקקקק'
    """)
    assert cur.fetchone()[0] == 0


# ─── MEANING SEARCH ──────────────────────────────────────────


def test_search_by_meaning_returns_results(cur):
    cur.execute("""
        SELECT DISTINCT ON (lemma_id)
            lemma_hebrew,
            lemma_meaning,
            part_of_speech,
            lemma_transcription
        FROM v_word_full
        WHERE lemma_meaning ILIKE '%peace%'
        ORDER BY lemma_id
    """)
    rows = cur.fetchall()
    assert len(rows) > 0


def test_search_by_meaning_results_contain_keyword(cur):
    """Every result should actually contain the search term in its meaning"""
    cur.execute("""
        SELECT DISTINCT lemma_meaning
        FROM v_word_full
        WHERE lemma_meaning ILIKE '%peace%'
    """)
    meanings = [row[0] for row in cur.fetchall()]
    assert all('peace' in m.lower() for m in meanings)


def test_search_by_meaning_no_results(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_word_full
        WHERE lemma_meaning ILIKE '%zzzzzzzzz%'
    """)
    assert cur.fetchone()[0] == 0


# ─── TRANSCRIPTION SEARCH ────────────────────────────────────


def test_search_by_transcription_exact_match(cur):
    """katavti should return score 1.0 exact match"""
    cur.execute("""
        WITH results AS (
            SELECT DISTINCT ON (lemma_id)
                lemma_hebrew,
                lemma_meaning,
                part_of_speech,
                cell_hebrew,
                cell_transcription,
                cell_meaning,
                labels,
                similarity(cell_transcription_plain, 'katavti') AS score
            FROM v_cell_search
            WHERE cell_transcription_plain % 'katavti'
            ORDER BY lemma_id, score DESC
        )
        SELECT * FROM results WHERE score = 1.0
    """)
    rows = cur.fetchall()
    assert len(rows) > 0
    assert all(row[-1] == 1.0 for row in rows)


def test_search_by_transcription_fuzzy_fallback(cur):
    """catavti is wrong spelling but should still find results via fuzzy"""
    cur.execute("""
        WITH results AS (
            SELECT DISTINCT ON (lemma_id)
                lemma_hebrew,
                lemma_meaning,
                part_of_speech,
                cell_hebrew,
                cell_transcription,
                cell_meaning,
                labels,
                similarity(cell_transcription_plain, 'catavti') AS score
            FROM v_cell_search
            WHERE cell_transcription_plain % 'catavti'
            ORDER BY lemma_id, score DESC
        )
        SELECT * FROM results
        WHERE score < 1.0
        ORDER BY score DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    assert len(rows) > 0


def test_search_by_transcription_exact_suppresses_fuzzy(cur):
    """when exact match exists, fuzzy results should not appear"""
    cur.execute("""
        WITH results AS (
            SELECT DISTINCT ON (lemma_id)
                similarity(cell_transcription_plain, 'katavti') AS score
            FROM v_cell_search
            WHERE cell_transcription_plain % 'katavti'
            ORDER BY lemma_id, score DESC
        )
        SELECT * FROM results WHERE score = 1.0
    """)
    exact = cur.fetchall()

    cur.execute("""
        WITH results AS (
            SELECT DISTINCT ON (lemma_id)
                similarity(cell_transcription_plain, 'katavti') AS score
            FROM v_cell_search
            WHERE cell_transcription_plain % 'katavti'
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
    fuzzy = cur.fetchall()

    assert len(exact) > 0
    assert len(fuzzy) == 0


def test_search_by_transcription_no_results(cur):
    cur.execute("""
        SELECT COUNT(*) FROM v_cell_search
        WHERE cell_transcription_plain % 'zzzzzzzzzzz'
    """)
    assert cur.fetchone()[0] == 0


# ─── PART OF SPEECH SEARCH ───────────────────────────────────


def test_search_by_pos_hifil_returns_results(cur):
    cur.execute("""
        SELECT DISTINCT ON (lemma_id)
            lemma_hebrew,
            lemma_meaning,
            part_of_speech
        FROM v_cell_search
        WHERE part_of_speech_plain ILIKE '%hifil%'
        ORDER BY lemma_id
        LIMIT 10
    """)
    rows = cur.fetchall()
    assert len(rows) > 0


def test_search_by_pos_results_contain_hifil(cur):
    cur.execute("""
        SELECT DISTINCT part_of_speech_plain
        FROM v_cell_search
        WHERE part_of_speech_plain ILIKE '%hifil%'
    """)
    pos_values = [row[0] for row in cur.fetchall()]
    assert all('hifil' in p.lower() for p in pos_values)


def test_search_by_pos_with_root(cur):
    """hifil search should expose root data"""
    cur.execute("""
        SELECT DISTINCT ON (lemma_id)
            root_display,
            lemma_hebrew,
            lemma_meaning,
            part_of_speech
        FROM v_cell_search
        WHERE part_of_speech_plain ILIKE '%hifil%'
        ORDER BY lemma_id
        LIMIT 10
    """)
    rows = cur.fetchall()
    assert len(rows) > 0



    # ─── ROOT SEARCH ─────────────────────────────────────────────


def test_search_by_root_returns_results(cur):
    """כתב root should return multiple lemmas"""
    cur.execute("""
        SELECT DISTINCT ON (l.id)
            r.display        AS root_display,
            r.normalized     AS root_normalized,
            l.hebrew         AS lemma_hebrew,
            l.meaning        AS lemma_meaning,
            l.part_of_speech
        FROM roots r
        JOIN lemmas l ON l.root_id = r.id
        WHERE r.normalized = 'כתב'
        ORDER BY l.id
    """)
    rows = cur.fetchall()
    assert len(rows) > 0


def test_search_by_root_all_lemmas_share_root(cur):
    """every result should belong to the searched root"""
    cur.execute("""
        SELECT DISTINCT r.normalized
        FROM roots r
        JOIN lemmas l ON l.root_id = r.id
        WHERE r.normalized = 'כתב'
    """)
    roots = {row[0] for row in cur.fetchall()}
    assert roots == {'כתב'}


def test_search_by_root_no_results(cur):
    cur.execute("""
        SELECT COUNT(*) FROM roots r
        JOIN lemmas l ON l.root_id = r.id
        WHERE r.normalized = 'קקקק'
    """)
    assert cur.fetchone()[0] == 0