import json
import re

# Input and output file paths
input_file = 'bbe_cleaned.txt'
output_file = 'load_bbe_data.jsonl'

# Bible version and denominations
translation = "BBE"
version_info = "Bible in Basic English - public domain"
denominations = [
    "Seeker Friendly",
    "Basic Literacy Missions",
    "ESL (English as a Second Language)",
    "Children’s Ministry",
    "Bible Translation Introductory Programs"
]

# Function to parse line like "GEN 1:1 ..." into structured data
def parse_line(line):
    match = re.match(r'^(\w+)\s+(\d+):(\d+)\s+(.*)$', line)
    if not match:
        return None
    book_abbr, chapter, verse, text = match.groups()
    return {
        "book": book_abbr,
        "chapter": int(chapter),
        "verse": int(verse),
        "reference": f"{book_abbr} {chapter}:{verse}",
        "text": text.strip(),
        "translation": translation,
        "version_info": version_info,
        "denominations": denominations
    }

# Read input and write JSONL
with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        entry = parse_line(line)
        if entry:
            outfile.write(json.dumps(entry, ensure_ascii=False) + '\n')

print(f"✅ Done. Output saved to {output_file}")
