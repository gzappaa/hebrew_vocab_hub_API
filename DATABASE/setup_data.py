#!/usr/bin/env python3
from pathlib import Path
import urllib.request

DATA_URL = (
    "https://drive.usercontent.google.com/download"
    "?id=1otMBzora9d2pPmaaOQja791ZyMgrHZLD"
    "&export=download"
    "&confirm=t"
)

BASE_DIR = Path(__file__).resolve().parent.parent  # goes up to hebrew_vocab_hub/
DATA_PATH = BASE_DIR / "DATABASE" / "vocab_dataset.json"
ENV_EXAMPLE = BASE_DIR / ".env.example"
ENV_FILE = BASE_DIR / ".env"
ENV_PROD_EXAMPLE = BASE_DIR / "API" / ".env.prod.example"
ENV_PROD_FILE = BASE_DIR / "API" / ".env.prod"


def setup_env():
    if not ENV_FILE.exists():
        ENV_EXAMPLE.rename(ENV_FILE)
        print("Created .env")
    else:
        print(".env already exists, skipping.")

    if not ENV_PROD_FILE.exists():
        ENV_PROD_EXAMPLE.rename(ENV_PROD_FILE)
        print("Created API/.env.prod")
    else:
        print("API/.env.prod already exists, skipping.")



def download_data():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DATA_PATH.exists():
        print("Data already exists, skipping.")
        return

    print("Downloading dataset...")
    urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    print("Done.")


if __name__ == "__main__":
    setup_env()
    download_data()