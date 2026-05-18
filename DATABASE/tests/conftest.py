import os
import pytest
import psycopg2

from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def conn():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=os.getenv("POSTGRESQL_PORT"),
        dbname=os.getenv("TEST_POSTGRESQL_DBNAME"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD"),
    )
    yield conn
    conn.close()

@pytest.fixture(scope="session")
def cur(conn):
    cur = conn.cursor()
    yield cur
    cur.close()

@pytest.fixture(scope="session")
def cur(conn):
    conn.autocommit = True
    cur = conn.cursor()
    yield cur
    cur.close()