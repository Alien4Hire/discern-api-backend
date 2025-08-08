import os, time, sys, json
import requests

ES = os.getenv("ELASTIC_HOST", "http://elasticsearch:9200").rstrip("/")
INDEX = os.getenv("ELASTIC_INDEX", "bible_verses")
DATA_DIR = os.getenv("DATA_DIR", "/app/seed_data")
FILES = ["load_kjv_data.jsonl", "load_web_data.jsonl", "load_bbe_data.jsonl"]

def wait_for_es(max_wait=180):
    url = f"{ES}/_cluster/health"
    start = time.time()
    while True:
        try:
            r = requests.get(url, timeout=3)
            if r.ok:
                s = r.json().get("status")
                print(f"ES health: {s}")
                if s in ("yellow", "green"):
                    return
            else:
                print(f"ES not ready, HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"ES not reachable yet: {e}")
        if time.time() - start > max_wait:
            print("Timed out waiting for Elasticsearch.")
            sys.exit(1)
        time.sleep(3)

def ensure_index():
    mapping = {
        "mappings": {
            "properties": {
                "book": {"type": "keyword"},
                "chapter": {"type": "integer"},
                "verse": {"type": "integer"},
                "reference": {"type": "text"},
                "text": {"type": "text"},
                "translation": {"type": "keyword"},
                "denominations": {"type": "keyword"}
            }
        }
    }
    r = requests.head(f"{ES}/{INDEX}")
    if r.status_code == 404:
        print(f"Creating index {INDEX}…")
        r = requests.put(f"{ES}/{INDEX}", json=mapping)
        r.raise_for_status()
    else:
        print(f"Index {INDEX} already exists.")

def bulk_load():
    for name in FILES:
        path = os.path.join(DATA_DIR, name)
        if not os.path.exists(path):
            print(f"Missing file: {path} (skipping)")
            continue
        print(f"Loading {name} …")
        lines = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lines.append('{"index":{}}')
                lines.append(line)
        ndjson = "\n".join(lines) + "\n"
        r = requests.post(f"{ES}/{INDEX}/_bulk", data=ndjson,
                          headers={"Content-Type": "application/x-ndjson"})
        r.raise_for_status()
        resp = r.json()
        if resp.get("errors"):
            print("Bulk had errors; first item:", json.dumps(resp["items"][0], indent=2))
        print(f"Finished {name}")

if __name__ == "__main__":
    print(f"Connecting to ES at {ES}")
    wait_for_es()
    ensure_index()
    bulk_load()
    # quick count
    r = requests.get(f"{ES}/{INDEX}/_count")
    print("Count:", r.json())
