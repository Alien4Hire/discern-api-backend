import os
import json
import time
from typing import Iterator, Dict, Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elastic_transport import ConnectionError as ESConnectionError

ELASTIC_HOST = os.environ.get("ELASTIC_HOST", "http://elasticsearch:9200")
INDEX = os.environ.get("ELASTIC_INDEX", "bible_verses")
DATA_DIR = os.getenv("DATA_DIR", "/app/seed_data")
FILES = ["load_kjv_data.jsonl", "load_web_data.jsonl", "load_bbe_data.jsonl"]

MAPPING = {
    "mappings": {
        "properties": {
            "book": {"type": "keyword"},
            "chapter": {"type": "integer"},
            "verse": {"type": "integer"},
            "reference": {"type": "keyword"},
            "text": {"type": "text"},
            "translation": {"type": "keyword"},
            "denominations": {"type": "keyword"}
        }
    }
}

def wait_for_es(es: Elasticsearch, timeout: int = 180, interval: float = 2.5) -> None:
    """Wait until Elasticsearch responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if es.ping():
                print("✅ Elasticsearch is up")
                return
        except ESConnectionError:
            pass
        except Exception as e:
            print(f"Elasticsearch not ready yet: {e}")
        print("⌛ Waiting for Elasticsearch...")
        time.sleep(interval)
    raise RuntimeError(f"Timed out waiting for Elasticsearch at {ELASTIC_HOST}")

def docs_from_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            yield {"_index": INDEX, "_source": doc}

def main():
    print(f"🔌 Connecting to ES at: {ELASTIC_HOST}")
    es = Elasticsearch(ELASTIC_HOST)

    wait_for_es(es)

    if not es.indices.exists(index=INDEX):
        es.indices.create(index=INDEX, body=MAPPING)
        print(f"📖 Created index: {INDEX}")
    else:
        print(f"✅ Index exists: {INDEX}")

    for filename in FILES:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"⚠️ Skipping, not found: {path}")
            continue

        print(f"📥 Loading {filename}...")
        success, errors = bulk(es, docs_from_jsonl(path), raise_on_error=False)
        print(f"✅ Finished {filename}: indexed={success}, errors={len(errors) if errors else 0}")
        if errors:
            print("⚠️ Sample errors:", errors[:3])

    es.indices.refresh(index=INDEX)
    print("🎉 Done.")

if __name__ == "__main__":
    main()
