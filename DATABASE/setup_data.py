#!/usr/bin/env python3
import urllib.request
import os

DATA_URL = (
    "https://drive.usercontent.google.com/download"
    "?id=1otMBzora9d2pPmaaOQja791ZyMgrHZLD"
    "&export=download"
    "&confirm=t"
)

DATA_PATH = "DATABASE/vocab_dataset.json"


def download_data():
    os.makedirs("DATABASE", exist_ok=True)

    if os.path.exists(DATA_PATH):
        print("Data already exists, skipping.")
        return

    print("Downloading dataset...")
    urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    print("Done.")


if __name__ == "__main__":
    download_data()