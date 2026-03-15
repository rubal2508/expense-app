import sys
import csv
import glob
import os
from collections import defaultdict
from categories import Category

# Categories excluded from "Total Expenses"
EXCLUDE_FROM_EXPENSES = {Category.TRANSFER_INTERNAL.value, Category.TRANSFER_EXTERNAL.value, Category.INVESTMENT}
# Category whose credits count as income
INCOME_CATEGORY = Category.TRANSFER_EXTERNAL.value

# Rows in the analysis — all categories except transfers, in enum definition order
ANALYSIS_CATEGORIES = [
    c.value for c in Category
    if c not in (Category.TRANSFER_EXTERNAL, Category.TRANSFER_INTERNAL)
]


# ── Data loading ──────────────────────────────────────────────────────────────────

def load_expenses(csv_path: str):
    """
    Read expenses CSV and return:
      debit[person][category]  -> total debit
      credit[person][category] -> total credit
    """
    debit  = defaultdict(lambda: defaultdict(float))
    credit = defaultdict(lambda: defaultdict(float))

    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            person   = (row.get('Person')   or '').strip()
            category = (row.get('Category') or '').strip().upper()
            cr       = row.get('Credit', '').strip()
            db       = row.get('Debit',  '').strip()

            if not person or not category:
                continue
            if db:
                debit[person][category]  += float(db)
            if cr:
                credit[person][category] += float(cr)

    return debit, credit


# ── Analysis CSV builder ──────────────────────────────────────────────────────────

def build_analysis(csv_path: str, out_path: str):
    debit, credit = load_expenses(csv_path)

    all_persons    = sorted(set(debit) | set(credit))
    all_categories = ANALYSIS_CATEGORIES   # fixed enum order, transfers excluded

    if not all_persons:
        print(f'⚠️  No data found in {csv_path}')
        return

    headers = ['Category'] + all_persons + ['Total']
    rows = []

    # ── Category rows ─────────────────────────────────────────────────────────────
    for cat in all_categories:
        row_total = 0.0
        row = {'Category': cat}
        for person in all_persons:
            val = debit[person].get(cat, 0.0)
            row[person] = round(val, 2) if val else ''
            row_total += val
        row['Total'] = round(row_total, 2)
        rows.append(row)

    # ── Total Expenses row ────────────────────────────────────────────────────────
    exp_row = {'Category': 'Total Expenses'}
    grand_exp = 0.0
    for person in all_persons:
        total = sum(
            v for cat, v in debit[person].items()
            if cat not in EXCLUDE_FROM_EXPENSES
        )
        exp_row[person] = round(total, 2)
        grand_exp += total
    exp_row['Total'] = round(grand_exp, 2)
    rows.append(exp_row)

    # ── Total Income row ──────────────────────────────────────────────────────────
    inc_row = {'Category': 'Total Income'}
    grand_inc = 0.0
    for person in all_persons:
        total = credit[person].get(INCOME_CATEGORY, 0.0)
        inc_row[person] = round(total, 2) if total else ''
        grand_inc += total
    inc_row['Total'] = round(grand_inc, 2) if grand_inc else ''
    rows.append(inc_row)

    # ── Write ─────────────────────────────────────────────────────────────────────
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f'✅  {os.path.basename(csv_path)} → {os.path.basename(out_path)}')
    print(f'   Persons    : {", ".join(all_persons)}')
    print(f'   Categories : {len(all_categories)}')


# ── Derive output filename ────────────────────────────────────────────────────────

def derive_out_path(in_path: str) -> str:
    directory = os.path.dirname(in_path) or '.'
    basename  = os.path.basename(in_path)
    out_name  = basename.replace('expenses', 'analysis', 1)
    return os.path.join(directory, out_name)


# ── Main ──────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Collect input files — supports glob patterns and explicit paths
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

    for in_file in input_files:
        out_file = derive_out_path(in_file)
        build_analysis(in_file, out_file)
