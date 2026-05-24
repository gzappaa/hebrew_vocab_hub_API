#!/usr/bin/env python3
"""
init_db.py
Run automatically by Docker on first start.
Checks if DB is empty, imports data if needed.
"""
import os
import sys
import json
import psycopg2
from pathlib import Path

# when running inside docker-entrypoint-initdb.d
sys.path.insert(0, "/docker-entrypoint-initdb.d")
from import_vocab import import_vocab

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   os.getenv("POSTGRES_DB"),
    "user":     os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

JSON_PATH = Path("/docker-entrypoint-initdb.d/vocab_dataset.json")

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM lemmas;")
count = cur.fetchone()[0]
cur.close()

if count > 0:
    print(f"Data already imported ({count} lemmas). Skipping.")
    conn.close()
    sys.exit(0)

print("Database empty. Importing data...")
with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

import_vocab(conn, data)
conn.close()
print("Done.")