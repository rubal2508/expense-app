import re
import sys
import csv
import json
import hashlib
from datetime import datetime
from categories import Category, CATEGORY_ALIASES, normalise_category

# ── Description map ───────────────────────────────────────────────────────────────

def load_description_map(path: str = 'description_map.json') -> dict:
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ── Regex Patterns ────────────────────────────────────────────────────────────────

MSG_RE = re.compile(
    r'^\[(\d{2}/\d{2}/\d{2}),\s+(\d{1,2}:\d{2}:\d{2}[\s\u202f]+[AP]M)\]\s+([^:]+):\s+(.+)$',
    re.DOTALL
)

FOREIGN_SUFFIX_RE = re.compile(
    r'^\s*[+\-]?\s*(?:₹\s*)?\d[\d,]*(?:\.\d+)?\s*(?:usd|eur|gbp|sgd|aed|myr|thb)\b',
    re.IGNORECASE
)

EXPENSE_RE = re.compile(
    r'^([+\-])?\s*(?:₹\s*)?'
    r'(\d[\d,]*(?:\.\d+)?(?:\s*(?:k|lakh|lac))?)'
    r'\s+(.+)$',
    re.IGNORECASE
)

CATEGORY_RE  = re.compile(r'\[([^\]]+)\]')
EDITED_RE    = re.compile(r'[\s\u200e]*<This message was edited>\s*$')
DELETED_RE   = re.compile(r'(You deleted this message|This message was deleted)', re.IGNORECASE)

IGNORE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r'^[\u200e\u202f]*Messages and calls are end-to-end encrypted',
        r'^[\u200e\u202f]*You (created|deleted|added|removed|changed|left)',
        r'^[\u200e\u202f]*(image|sticker|video|audio|document|GIF) omitted',
        r'^[\u200e\u202f]*This message was deleted',
        r'^[\u200e\u202f]*You deleted this message',
        r'^[\u200e\u202f]+$',
        r'^\s*$',
    ]
]

# ── Helpers ───────────────────────────────────────────────────────────────────────

def make_key(*parts) -> str:
    raw = '|'.join(str(p).strip().lower() for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


def fmt_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, '%d/%m/%y').strftime('%d %b %Y')
    except ValueError:
        return date_str


def normalise_amount(raw: str, sign):
    raw = raw.strip().lower().replace(',', '')
    multiplier = 1.0
    if raw.endswith('lakh') or raw.endswith('lac'):
        raw = re.sub(r'(lakh|lac)$', '', raw).strip()
        multiplier = 100_000.0
    elif raw.endswith('k'):
        raw = raw[:-1].strip()
        multiplier = 1_000.0
    try:
        amount = float(raw) * multiplier
        return round(-amount if sign == '-' else amount, 2)
    except ValueError:
        return None


def extract_category(text: str):
    m = CATEGORY_RE.search(text)
    if m:
        return normalise_category(m.group(1).strip()), CATEGORY_RE.sub('', text).strip()
    return '', text


def is_ignored(body: str) -> bool:
    return any(p.search(body) for p in IGNORE_PATTERNS)

# ── Message grouping ──────────────────────────────────────────────────────────────

def group_messages(lines):
    """Return list of (start_line_no, full_message_text)."""
    messages, current_no, current = [], None, None
    for i, raw in enumerate(lines, 1):
        stripped = raw.rstrip('\n').strip()
        if MSG_RE.match(stripped):
            if current is not None:
                messages.append((current_no, current))
            current_no, current = i, stripped
        elif current is not None and stripped:
            current += '\n' + stripped
    if current is not None:
        messages.append((current_no, current))
    return messages

# ── Core parser ───────────────────────────────────────────────────────────────────

def parse_chat(filepath: str, month_label: str = None):
    """
    Parse the chat file. If month_label is given (e.g. 'feb_2026') only
    messages from that month are included.
    """
    parsed, unparsed = [], []
    desc_map = load_description_map()

    month_filter = None
    if month_label:
        dt = datetime.strptime(f'01_{month_label}', '%d_%b_%Y')
        month_filter = (dt.month, dt.year)

    with open(filepath, encoding='utf-8') as f:
        raw_lines = f.readlines()

    for line_no, msg in group_messages(raw_lines):
        msg = EDITED_RE.sub('', msg)
        m   = MSG_RE.match(msg)
        if not m:
            continue

        date_str, _, person, body = m.groups()
        person, body = person.strip(), body.strip()
        date_fmt = fmt_date(date_str)

        if month_filter:
            try:
                msg_dt = datetime.strptime(date_fmt, '%d %b %Y')
                if (msg_dt.month, msg_dt.year) != month_filter:
                    continue
            except ValueError:
                continue

        if is_ignored(body):
            continue

        for sub in body.splitlines():
            sub = sub.strip()
            if not sub or is_ignored(sub):
                continue
            if DELETED_RE.search(sub):
                continue

            # Foreign currency
            if FOREIGN_SUFFIX_RE.match(sub):
                unparsed.append({
                    'line_no': line_no, 'date': date_fmt, 'person': person,
                    'text': sub, 'reason': 'Foreign currency — manual review needed',
                    'key': make_key(date_fmt, person, sub),
                })
                continue

            # Must start with digit
            bare = sub.lstrip('+-').lstrip()
            if not bare or not bare[0].isdigit():
                unparsed.append({
                    'line_no': line_no, 'date': date_fmt, 'person': person,
                    'text': sub, 'reason': 'Does not start with a number',
                    'key': make_key(date_fmt, person, sub),
                })
                continue

            exp_m = EXPENSE_RE.match(sub)
            if exp_m:
                sign, amount_raw, text_raw = exp_m.groups()
                if sign == '-':
                    unparsed.append({
                        'line_no': line_no, 'date': date_fmt, 'person': person,
                        'text': sub, 'reason': 'Negative amount — manual review needed',
                        'key': make_key(date_fmt, person, sub),
                    })
                    continue
                amount = normalise_amount(amount_raw, sign)
                if amount is not None:
                    category, description = extract_category(text_raw)
                    if not category:
                        category = desc_map.get(description.strip().lower(), '')
                    if not category:
                        for word in re.findall(r'\b\w+\b', description.lower()):
                            if word in CATEGORY_ALIASES:
                                category = CATEGORY_ALIASES[word].value
                                break
                    if not category and re.search(r'\binvest(ment)?\b', description, re.IGNORECASE):
                        category = Category.INVESTMENT.value
                    parsed.append({
                        'line_no': line_no, 'date': date_fmt, 'person': person,
                        'amount': amount, 'is_credit': sign == '+',
                        'category': category, 'description': description,
                        'key': make_key(date_fmt, person, amount, description),
                    })
                else:
                    unparsed.append({
                        'line_no': line_no, 'date': date_fmt, 'person': person,
                        'text': sub, 'reason': 'Could not parse amount',
                        'key': make_key(date_fmt, person, sub),
                    })
            else:
                unparsed.append({
                    'line_no': line_no, 'date': date_fmt, 'person': person,
                    'text': sub, 'reason': 'No expense pattern matched',
                    'key': make_key(date_fmt, person, sub),
                })

    _stamp_occurrence_keys(parsed)
    _stamp_occurrence_keys(unparsed)
    return parsed, unparsed


def _stamp_occurrence_keys(rows):
    """
    Append an occurrence index to each key so that two identical expenses on
    the same day by the same person get distinct keys (_0, _1, _2 …).
    """
    counts = {}
    for row in rows:
        base       = row['key']
        idx        = counts.get(base, 0)
        row['key'] = f'{base}_{idx}'
        counts[base] = idx + 1


# ── Read existing keys from CSV ───────────────────────────────────────────────────

def load_existing_keys(exp_csv: str, rev_csv: str):
    """Return (expense_keys, review_keys) already present in the CSV files."""
    def read_keys(path, key_col):
        keys = set()
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    val = row.get(key_col, '').strip()
                    if val:
                        keys.add(val)
        except FileNotFoundError:
            pass
        return keys

    return read_keys(exp_csv, '_key'), read_keys(rev_csv, '_key')


# ── Write CSV files ───────────────────────────────────────────────────────────────

EXP_FIELDS = ['Date', 'Person', 'Credit', 'Debit', 'Category', 'Description', '_key']
REV_FIELDS = ['Line #', 'Date', 'Person', 'Raw Text', 'Reason', '_key']


def _write_csv(path, fieldnames, rows, write_header):
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def update_csv(parsed: list, unparsed: list, exp_csv: str, rev_csv: str):
    """Append only new rows to each CSV, deduplicating via _key column."""
    import os
    existing_exp_keys, existing_rev_keys = load_existing_keys(exp_csv, rev_csv)

    new_parsed   = [r for r in parsed   if r['key'] not in existing_exp_keys]
    new_unparsed = [r for r in unparsed if r['key'] not in existing_rev_keys]

    if new_parsed:
        exp_rows = [
            {
                'Date':        r['date'],
                'Person':      r['person'],
                'Credit':      r['amount'] if r.get('is_credit') else '',
                'Debit':       r['amount'] if not r.get('is_credit') else '',
                'Category':    r['category'],
                'Description': r['description'],
                '_key':        r['key'],
            }
            for r in new_parsed
        ]
        _write_csv(exp_csv, EXP_FIELDS, exp_rows, write_header=not os.path.exists(exp_csv))

    if new_unparsed:
        rev_rows = [
            {
                'Line #':   r.get('line_no', ''),
                'Date':     r.get('date',    ''),
                'Person':   r.get('person',  ''),
                'Raw Text': r.get('text',    ''),
                'Reason':   r.get('reason',  ''),
                '_key':     r.get('key',     ''),
            }
            for r in new_unparsed
        ]
        _write_csv(rev_csv, REV_FIELDS, rev_rows, write_header=not os.path.exists(rev_csv))

    # ── Summary ───────────────────────────────────────────────────────────────────
    skipped_exp = len(parsed)   - len(new_parsed)
    skipped_rev = len(unparsed) - len(new_unparsed)

    print(f'✅  Saved → {exp_csv}  |  {rev_csv}')
    print(f'   New expense rows   : {len(new_parsed):>4}   (skipped {skipped_exp} duplicates)')
    print(f'   New review rows    : {len(new_unparsed):>4}   (skipped {skipped_rev} duplicates)')
    print(f'   Total in file      : {len(existing_exp_keys) + len(new_parsed):>4} expenses  |  '
          f'{len(existing_rev_keys) + len(new_unparsed)} needs review')


# ── Main ──────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    chat_file   = sys.argv[1] if len(sys.argv) > 1 else '_chat.txt'
    month_label = sys.argv[2] if len(sys.argv) > 2 else None   # e.g. 'feb_2026'

    if month_label:
        exp_csv = f'expenses_{month_label}.csv'
        rev_csv = f'needs_review_{month_label}.csv'
    else:
        exp_csv = 'expenses.csv'
        rev_csv = 'needs_review.csv'

    parsed, unparsed = parse_chat(chat_file, month_label)
    update_csv(parsed, unparsed, exp_csv, rev_csv)
