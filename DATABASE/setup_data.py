#!/usr/bin/env python3
from pathlib import Path
import urllib.request

DATA_URL = (
    "https://drive.usercontent.google.com/download"
    "?id=1otMBzora9d2pPmaaOQja791ZyMgrHZLD"
    "&export=download"
    "&confirm=t"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "DATABASE" / "vocab_dataset.json"


def download_data():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DATA_PATH.exists():
        print("Data already exists, skipping.")
        return

    print("Downloading dataset...")
    urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    print("Done.")


if __name__ == "__main__":
    download_data()