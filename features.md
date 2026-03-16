# Feature Requests & Change Log

## Parsing & Data Extraction
- Parse WhatsApp chat export and convert expense messages into a structured file
- Handle unparsable lines gracefully — store them separately for manual review
- In Needs Review output: parse date and person where possible, store remainder as raw text
- Add line number column to Needs Review so messages can be traced back to the chat file
- Foreign currency amounts (USD, EUR, etc.) go to Needs Review
- Ignore system messages (encryption notice, group events, etc.)
- Ignore image / sticker / video / audio / document omitted lines
- Ignore deleted messages
- Messages that do not start with a number go to Needs Review
- Messages with a "-" prefixed amount go to Needs Review

## Categories
- Add a Category column; messages tagged `#string` get `category = string`
- `#tag` resolves via USER_OVERRIDES → exact enum match → underscore-normalised enum match; unrecognised tags fall back to empty so the alias scan can take over
- Shorthand hashtags supported (e.g. `#internaltransfer` → TRANSFER_INTERNAL) via underscore normalisation or USER_OVERRIDES
- Messages containing keyword "invest" or "investment" get `category = INVESTMENT` (via USER_OVERRIDES)
- Normalise duplicate category variants ("invest" vs "investment") using a Category enum
- Update Category enum values to match the full app category list
- Extract Category enum and aliases into `categories.py`, shared across all scripts
- Single `USER_OVERRIDES` dict in `categories.py` for all keyword and #hashtag shortcuts
- Fuzzy alias matching via `difflib.get_close_matches` catches common spelling mistakes
- Full-phrase alias scan (longest match first) fixes multi-word aliases like "south table", "mutual fund"

## Output Format
- Split Amount into two columns: Credit ("+") and Debit (no sign); "-" goes to Needs Review
- Remove the Total row from the bottom of the Expenses sheet
- Do not auto-open the output file after the runner finishes; close the terminal window after pressing Enter
- Switch output format from .xlsx to CSV
- Output filenames include month-year suffix: `expenses_feb_2026.csv`, `needs_review_feb_2026.csv`
- Output files are organised into `resources/{month_label}/` subdirectories

## Analysis
- Add an Analysis sheet with monthly total expenses per person, excluding Investment and Credit rows
- Extract analysis into a standalone `analyse_expenses.py` script that reads a CSV and writes a new CSV
- Analysis CSV always contains all Category enum rows (except TRANSFER_EXTERNAL and TRANSFER_INTERNAL), in enum definition order — even if spend is zero
- `Total Expenses` row excludes TRANSFER_INTERNAL, TRANSFER_EXTERNAL, and INVESTMENT
- `Total Income` row shows sum of the Credit column where category is TRANSFER_EXTERNAL

## Deduplication & Incremental Updates
- Script appends to an existing output file and skips already-processed rows — no external database needed
- Deduplication uses an MD5 hash of (date, person, amount, description) stored in a hidden `_key` column
- Identical expenses from the same person on the same date get unique keys via an occurrence index suffix (`_0`, `_1`, …)

## Monthly Filtering
- `parse_expenses.py` processes one month at a time
- `run_expenses.command` prompts for month-year input (e.g. `feb 26`), defaulting to the previous month
- Month label is validated before the script runs

## Category Learning
- `description_map.json` acts as a persistent hashmap of description → category, survives across runs
- `learn_categories.py` reads expense CSVs and updates the map; last-seen value wins on conflict
- `parse_expenses.py` consults the map during parsing — after bracket notation but before the keyword/alias scan

## Project Structure
- `run_expenses.command` — double-clickable macOS runner for the parser
- `run_analysis.command` — double-clickable runner for the analyser
- `run_learn.command` — double-clickable runner for the category learner
- Python scripts moved to `scripts/`; runners stay in the project root
- Chat file renamed from `_chat.txt` to `main_chat.txt`
- `resources/` directory holds all personal data: chat file, description map, and all output CSVs

## Misc
- README created for the project
- Git repo initialised with `.gitignore` excluding all personal data (`resources/`, description map, chat files)
