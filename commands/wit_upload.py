import json
import os
import sys
import requests
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

WIT_API_URL = "https://api.wit.ai/utterances"
BATCH_SIZE = 200  # Safe batch size
WIT_TOKEN = os.getenv("WIT_TOKEN")

if not WIT_TOKEN:
    print("Error: WIT_TOKEN environment variable not set")
    sys.exit(1)


def load_utterances(file_path: Path) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_utterance(u: Dict, index: int):
    required_keys = {"text", "intent", "entities", "traits"}
    missing = required_keys - u.keys()
    if missing:
        raise ValueError(f"Utterance #{index} missing keys: {missing}")

    if not isinstance(u["text"], str) or not u["text"].strip():
        raise ValueError(f"Utterance #{index} has invalid text")

    if not isinstance(u["intent"], str) or not u["intent"].strip():
        raise ValueError(f"Utterance #{index} has invalid intent")

    if not isinstance(u["entities"], list):
        raise ValueError(f"Utterance #{index} entities must be a list")

    if not isinstance(u["traits"], list):
        raise ValueError(f"Utterance #{index} traits must be a list")


def deduplicate_utterances(utterances: List[Dict]) -> List[Dict]:
    deduped = {}
    for u in utterances:
        # last one wins if duplicates exist
        deduped[u["text"].strip().lower()] = u
    return list(deduped.values())


def chunk_utterances(utterances: List[Dict], size: int):
    for i in range(0, len(utterances), size):
        yield utterances[i:i + size]


def upload_batch(batch: List[Dict], batch_number: int):
    headers = {
        "Authorization": f"Bearer {WIT_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        WIT_API_URL,
        headers=headers,
        json=batch,
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Batch {batch_number} failed: "
            f"{response.status_code} {response.text}"
        )

    print(f"✔ Batch {batch_number} uploaded ({len(batch)} utterances)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_utterances.py utterances.json")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    print(f"Loading utterances from {file_path}")
    utterances = load_utterances(file_path)

    print("Validating utterances...")
    for i, u in enumerate(utterances):
        validate_utterance(u, i)

    original_count = len(utterances)
    utterances = deduplicate_utterances(utterances)

    print(f"Deduplicated: {original_count} → {len(utterances)}")

    print("Uploading utterances in batches...")
    for i, batch in enumerate(chunk_utterances(utterances, BATCH_SIZE), start=1):
        upload_batch(batch, i)

    print(" All utterances uploaded. Training triggered automatically.")

def load_utterances(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def upload_utterances(utterances):
    headers = {
        "Authorization": f"Bearer {WIT_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        WIT_API_URL,
        headers=headers,
        json=utterances
    )

    if response.status_code != 200:
        print("Upload failed:")
        print(response.status_code, response.text)
        sys.exit(1)

    return response.json()

def main():
    if len(sys.argv) < 2:
        print("Usage: python wit_upload.py utterances.v1.json")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    utterances = load_utterances(file_path)

    print(f"Uploading {len(utterances)} utterances...")
    result = upload_utterances(utterances)

    print("Upload successful. Training started automatically.")
    print(result)

if __name__ == "__main__":
    # main()
    temp = load_utterances("/wit_training_data/utterances.v1.json")
    upload_utterances(temp)
