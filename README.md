# WhatsApp Expense Parser

Parse a WhatsApp group chat export into structured CSV files for shared expense tracking. Supports incremental updates, automatic category detection, and monthly analysis reports.

---

## How it works

1. Export your WhatsApp group chat to a `.txt` file and place it in `resources/main_chat.txt`
2. Double-click `run_expenses.command` and enter the month you want to process
3. The script reads every message, extracts expenses, and writes two CSV files into `resources/{month}/`

On each run the script only processes the selected month and skips any rows already present in the output file — so re-running on an updated chat export is always safe.

---

## Project structure

```
expense_app/
├── run_expenses.command      # Parse chat → expenses CSV
├── run_analysis.command      # Generate analysis CSV from expenses
├── run_learn.command         # Learn description→category mappings
│
├── scripts/
│   ├── parse_expenses.py     # Core parser
│   ├── analyse_expenses.py   # Monthly analysis aggregator
│   ├── learn_categories.py   # Category map updater
│   └── categories.py         # Category enum and aliases (shared)
│
└── resources/                # Personal data — gitignored
    ├── main_chat.txt         # WhatsApp chat export (your input)
    ├── description_map.json  # Learned description → category map
    └── feb_2026/
        ├── expenses_feb_2026.csv
        ├── needs_review_feb_2026.csv
        └── analysis_feb_2026.csv
```

---

## Quick start

### 1. Export your WhatsApp chat

Open the group → ⋮ → More → Export chat → Without media. Rename the file to `main_chat.txt` and place it in the `resources/` folder.

### 2. Parse expenses

Double-click `run_expenses.command`. You will be prompted:

```
Enter month-year (e.g. feb 26) [default: feb 26]:
```

Press Enter to accept the default (last month), or type a month like `jan 26` or `mar 2026`. The script creates:

```
resources/feb_2026/
  expenses_feb_2026.csv
  needs_review_feb_2026.csv
```

### 3. Review and fix categories

Open `expenses_feb_2026.csv`. Rows with no category detected will have an empty Category column — fill these in manually. Then double-click `run_learn.command` to teach the script those mappings for future runs:

```
resources/feb_2026/expenses_feb_2026.csv → description_map.json updated
  New entries     :   12
  Updated entries :    3
```

### 4. Generate analysis

Double-click `run_analysis.command`. It reads all `resources/*/expenses_*.csv` files and writes a `analysis_{month}.csv` alongside each one:

```
resources/feb_2026/analysis_feb_2026.csv
```

### Command line usage

```bash
# Parse a specific month
PYTHONPATH=scripts python3 scripts/parse_expenses.py resources/main_chat.txt feb_2026

# Analyse a specific month
PYTHONPATH=scripts python3 scripts/analyse_expenses.py resources/feb_2026/expenses_feb_2026.csv

# Learn from all months
PYTHONPATH=scripts python3 scripts/learn_categories.py
```

---

## Expense message format

Messages are parsed if they match:

```
[+] [₹] AMOUNT [k | lakh | lac]  DESCRIPTION  [#CATEGORY]
```

### Parsed examples

| Message | Credit | Debit | Category | Description |
|---|---|---|---|---|
| `460 zomato` | | 460 | FOOD | zomato |
| `26k rent` | | 26000 | RENT | rent |
| `10700 Dior perfume #GROOMING` | | 10700 | GROOMING | Dior perfume |
| `1 lakh mutual funds #INVESTMENT` | | 100000 | INVESTMENT | mutual funds |
| `+50000 salary #TRANSFER_EXTERNAL` | 50000 | | TRANSFER_EXTERNAL | salary |
| `+50000 salary #externaltransfer` | 50000 | | TRANSFER_EXTERNAL | salary |
| `800 gym membership` | | 800 | GYM | gym membership |
| `500 electricity bill #HOME` | | 500 | HOME | electricity bill |

### Goes to Needs Review

| Message | Reason |
|---|---|
| `-500 refund` | Negative amount — manual review needed |
| `250 USD hotel` | Foreign currency |
| `Paid the cab driver` | Does not start with a number |
| `Let me check the bill` | Does not start with a number |

### Category detection order (highest priority first)

1. **Hashtag** — `#FOOD` or `#food` in the message always wins; also resolves shortcuts like `#internaltransfer`
2. **Description map** — learned from past manually corrected CSVs
3. **Alias scan** — full-phrase first (`south table`), then word-by-word (`zomato` → FOOD, `uber` → LOCAL_TRAVEL)
4. **Fuzzy match** — catches common typos (`resturant` → FOOD, `grocceries` → GROCERIES)
5. **Empty** — left blank for manual correction

---

## Categories

Defined in `scripts/categories.py`. All category values are uppercase.

| Category | Examples |
|---|---|
| `FOOD` | zomato, restaurant, dining |
| `GROCERIES` | grocery, supermarket |
| `LOCAL_TRAVEL` | uber, ola, cab, auto |
| `LONG_TRAVEL` | flight, airport |
| `RENT` | rent |
| `GYM` | gym |
| `MEDICAL` | doctor, medicine, pharmacy |
| `GROOMING` | haircut, salon, myntra |
| `SUBSCRIPTION` | netflix, subscription |
| `HOME` | furniture, appliances |
| `INVESTMENT` | mutual fund, stocks |
| `TRANSFER_EXTERNAL` | salary, income received |
| `TRANSFER_INTERNAL` | transfer between own accounts |
| `OTHER_ESSENTIALS` | |
| `OTHER_NON_ESSENTIALS` | |
| `TREATS_AND_GIFTS` | gifts, treats |
| `REGULAR_PARTY_VACATION` | weekend trip |
| `BIG_PARTY_VACATION` | international holiday |
| `SPECIAL` | one-off special expenses |
| `PERSONAL` | personal items |

To add a new alias (e.g. `swiggy` → FOOD) or a `#hashtag` shortcut, add a line to `USER_OVERRIDES` in `scripts/categories.py`:

```python
'swiggy':           Category.FOOD,
'internaltransfer': Category.TRANSFER_INTERNAL,
```

---

## Output files

### expenses_{month}.csv

| Column | Content |
|---|---|
| Date | DD Mon YYYY (e.g. `15 Feb 2026`) |
| Person | Sender name from WhatsApp |
| Credit | Amount for "+" prefixed messages |
| Debit | Amount for all regular expenses |
| Category | Detected or manually set category |
| Description | Message text with brackets removed |
| _key | MD5 deduplication hash (hidden) |

### needs_review_{month}.csv

| Column | Content |
|---|---|
| Line # | Line number in the source chat file |
| Date | Message date |
| Person | Sender name |
| Raw Text | Original message text |
| Reason | Why it wasn't auto-parsed |
| _key | MD5 deduplication hash |

### analysis_{month}.csv

Rows = all categories (in enum order), Columns = each person + Total.

```
Category,Alice,Bob,Total
FOOD,1200.00,800.00,2000.00
GROCERIES,450.00,,450.00
...
Total Expenses,18000.00,12000.00,30000.00
Total Income,50000.00,,50000.00
```

- **Total Expenses** — sum of Debit, excluding TRANSFER_INTERNAL, TRANSFER_EXTERNAL, INVESTMENT
- **Total Income** — sum of Credit where category is TRANSFER_EXTERNAL

---

## Deduplication

Each row gets an MD5 hash of `date | person | amount | description`, stored in the hidden `_key` column. On re-run, existing keys are read first and matching rows are skipped.

Two identical messages from the same person on the same day get distinct keys via an occurrence suffix (`_0`, `_1`, …), so duplicates are never collapsed incorrectly.

---

## Requirements

- Python 3.9+
- No external dependencies (uses only the standard library)
