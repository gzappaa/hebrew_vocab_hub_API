import pytest


def test_no_orphaned_word_lemmas(cur):
    cur.execute("""
        SELECT COUNT(*) FROM word_lemmas wl
        WHERE NOT EXISTS (SELECT 1 FROM words w WHERE w.id = wl.word_id)
        OR NOT EXISTS (SELECT 1 FROM lemmas l WHERE l.id = wl.lemma_id)
    """)
    assert cur.fetchone()[0] == 0


def test_no_orphaned_conj_cells(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells cc
        WHERE NOT EXISTS (SELECT 1 FROM conj_tables ct WHERE ct.id = cc.table_id)
    """)
    assert cur.fetchone()[0] == 0


def test_no_orphaned_conj_tables(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_tables ct
        WHERE NOT EXISTS (SELECT 1 FROM conj_cells cc WHERE cc.table_id = ct.id)
    """)
    assert cur.fetchone()[0] == 0


def test_no_empty_hebrew_in_cells(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells
        WHERE hebrew IS NULL
    """)
    assert cur.fetchone()[0] == 0


def test_no_empty_hebrew_in_lemmas(cur):
    cur.execute("""
        SELECT COUNT(*) FROM lemmas
        WHERE hebrew IS NULL OR hebrew = ''
    """)
    assert cur.fetchone()[0] == 0


def test_no_punctuation_in_hebrew_plain_cells(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells
        WHERE hebrew_plain ~ '[!?.,;:]'
    """)
    assert cur.fetchone()[0] == 0


def test_no_invisible_unicode_in_hebrew_plain_cells(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells
        WHERE hebrew_plain ~ '[\u200B-\u200F\u202A-\u202E\uFEFF]'
    """)
    assert cur.fetchone()[0] == 0


def test_transcription_plain_is_lowercase(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells
        WHERE transcription_plain != lower(transcription_plain)
    """)
    assert cur.fetchone()[0] == 0


def test_transcription_plain_no_apostrophes(cur):
    cur.execute("""
        SELECT COUNT(*) FROM conj_cells
        WHERE transcription_plain ~ %s
    """, ("'|'|'|`|ʼ",))
    assert cur.fetchone()[0] == 0


def test_no_lemmas_without_word_lemma(cur):
    cur.execute("""
        SELECT COUNT(*) FROM lemmas l
        WHERE NOT EXISTS (SELECT 1 FROM word_lemmas wl WHERE wl.lemma_id = l.id)
    """)
    assert cur.fetchone()[0] == 0