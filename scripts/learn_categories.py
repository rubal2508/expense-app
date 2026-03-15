"""
Reads one or more expenses CSV files and updates description_map.json.

Usage:
    python3 learn_categories.py                      # reads all expenses_*.csv
    python3 learn_categories.py expenses_feb_2026.csv
"""
import sys
import csv
import glob
import json
import os
from categories import Category

MAP_FILE = 'description_map.json'
VALID_CATEGORIES = {c.value for c in Category}


def load_map(path: str) -> dict:
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_map(path: str, data: dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f'✅  {path} saved  ({len(data)} entries total)')


def learn(csv_paths: list, map_file: str = MAP_FILE):
    mapping = load_map(map_file)
    added = updated = skipped = 0

    for csv_path in csv_paths:
        print(f'   Reading {os.path.basename(csv_path)} …')
        with open(csv_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                desc = (row.get('Description') or '').strip()
                cat  = (row.get('Category')    or '').strip().upper()

                if not desc or cat not in VALID_CATEGORIES:
                    skipped += 1
                    continue

                key = desc.lower()
                if mapping.get(key) == cat:
                    continue
                if key in mapping:
                    updated += 1
                else:
                    added += 1
                mapping[key] = cat

    save_map(map_file, mapping)
    print(f'   New entries     : {added}')
    print(f'   Updated entries : {updated}')
    print(f'   Skipped (no category / invalid) : {skipped}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        args = ['expenses_*.csv']

    input_files = []
    for arg in args:
        matched = glob.glob(arg)
        input_files.extend(sorted(matched) if matched else [arg])

    if not input_files:
        print('⚠️  No matching CSV files found.')
        sys.exit(1)

    learn(input_files)
