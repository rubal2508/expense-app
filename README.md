# Expense App

Parse WhatsApp group chat exports into a clean, formatted Excel spreadsheet for shared expense tracking.

## What it does

You export your WhatsApp group chat to a `.txt` file, drop it in the folder, and run the script. It reads every message, extracts expense entries (amounts, dates, who paid, category), and writes them into `expenses.xlsx` with two sheets:

- **Expenses** — all successfully parsed entries with a running total
- **Needs Review** — anything it couldn't parse automatically (foreign currencies, ambiguous entries), flagged with a reason

Re-running the script on an updated chat export is safe — it deduplicates against whatever's already in the Excel file using MD5 hashes, so you'll never get double entries.

## Quick start

**macOS (double-click):**

1. Export your WhatsApp chat: open the group → ⋮ → More → Export chat → Without media
2. Rename the exported file to `_chat.txt` and place it in this folder
3. Double-click `run_expenses.command`

The script auto-installs `openpyxl` if missing and opens the Excel file when done.

**Command line:**

```bash
python3 parse_expenses.py _chat.txt expenses.xlsx
```

Custom filenames work too:

```bash
python3 parse_expenses.py my_chat_export.txt my_expenses.xlsx
```

## Requirements

- Python 3
- `openpyxl` — installed automatically by `run_expenses.command`, or manually: `pip3 install openpyxl`

No other dependencies, no API keys, no database.

## Expense message format

Messages are parsed if they match:

```
[±] [₹] AMOUNT [k | lakh | lac] [description] [[category]]
```

**Examples:**

| Message | Amount | Description | Category |
|---|---|---|---|
| `460 zomato` | ₹460 | zomato | — |
| `26k transfer to cash reserve` | ₹26,000 | transfer to cash reserve | — |
| `10700 Dior perfume [personal]` | ₹10,700 | Dior perfume | personal |
| `1 lakh mutual funds` | ₹1,00,000 | mutual funds | — |
| `-500 refund received` | −₹500 | refund received | — |

Messages in foreign currencies (USD, EUR, SGD, etc.) are automatically moved to the **Needs Review** sheet.

WhatsApp system messages (encryption notices, media placeholders, group join/leave events) are silently ignored.

## Output

**Expenses sheet columns:**

| Column | Content |
|---|---|
| Date | DD Mon YYYY |
| Person | Sender name from WhatsApp |
| Amount (₹) | Parsed number, right-aligned |
| Category | Extracted from `[brackets]` in the message |
| Description | Full message text |

A `TOTAL` row with a SUM formula is added at the bottom and updated on each run.

**Needs Review sheet columns:**

| Column | Content |
|---|---|
| Line # | Line number in the source chat file |
| Date | Message date |
| Person | Sender name |
| Raw Text | Original message text |
| Reason | Why it wasn't auto-parsed |

## How deduplication works

Each entry gets an MD5 hash of `date | person | amount | description`. When the script runs, it reads the existing `_key` column (hidden, column F) from the Excel file and skips any rows whose hash already exists. This makes it safe to run repeatedly as the chat grows.

Identical messages sent on the same day by the same person get distinct suffixes (`_0`, `_1`, …) so they aren't collapsed.

## Project structure

```
expense_app/
├── parse_expenses.py      # Core parser and Excel writer
├── run_expenses.command   # macOS launcher (auto-installs deps, opens output)
├── _chat.txt              # WhatsApp chat export (your input file)
└── expenses.xlsx          # Generated output (created on first run)
```
