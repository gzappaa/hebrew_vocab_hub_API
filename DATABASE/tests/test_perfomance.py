# test_performance.py

def test_hebrew_search_uses_index(cur):
    cur.execute("""
        EXPLAIN SELECT DISTINCT ON (lemma_id)
            lemma_hebrew, lemma_meaning
        FROM v_cell_search
        WHERE cell_hebrew_plain = 'כתב'
        ORDER BY lemma_id, cell_id
    """)
    plan = ' '.join(row[0] for row in cur.fetchall())
    assert 'Seq Scan' not in plan


def test_transcription_search_uses_index(cur):
    cur.execute("""
        EXPLAIN SELECT DISTINCT ON (lemma_id)
            lemma_hebrew, lemma_meaning
        FROM v_cell_search
        WHERE cell_transcription_plain % 'katavti'
        ORDER BY lemma_id
    """)
    plan = ' '.join(row[0] for row in cur.fetchall())
    assert 'Seq Scan' not in plan




def test_root_search_uses_index(cur):
    cur.execute("""
        EXPLAIN SELECT DISTINCT ON (l.id)
            r.display, l.hebrew, l.meaning
        FROM roots r
        JOIN lemmas l ON l.root_id = r.id
        WHERE r.normalized = 'כתב'
        ORDER BY l.id
    """)
    plan = ' '.join(row[0] for row in cur.fetchall())
    assert 'Seq Scan' not in plan




def test_meaning_search_uses_index(cur):
    cur.execute("""
        EXPLAIN SELECT DISTINCT ON (lemma_id)
            lemma_hebrew, lemma_meaning
        FROM v_word_full
        WHERE lemma_meaning ILIKE '%peace%'
        ORDER BY lemma_id
    """)
    plan = ' '.join(row[0] for row in cur.fetchall())
    assert 'idx_lemmas_meaning_trgm' in plan


def test_pos_search_uses_index(cur):
    cur.execute("""
        EXPLAIN SELECT DISTINCT ON (lemma_id)
            lemma_hebrew, lemma_meaning
        FROM v_cell_search
        WHERE part_of_speech_plain ILIKE '%hifil%'
        ORDER BY lemma_id
    """)
    plan = ' '.join(row[0] for row in cur.fetchall())
    assert 'idx_lemmas_pos_trgm' in plan