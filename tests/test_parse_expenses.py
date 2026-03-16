"""
Tests for parse_expenses.py and categories.py

Run from the project root:
    PYTHONPATH=scripts python3 -m pytest tests/
    # or without pytest:
    PYTHONPATH=scripts python3 tests/test_parse_expenses.py
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from parse_expenses import extract_date_override, _infer_year, extract_category, parse_chat
from categories import normalise_category


# ── Helpers ───────────────────────────────────────────────────────────────────

def wa_msg(date, name, body, time='10:00:00 AM'):
    """Build a WhatsApp-formatted message line."""
    return f'[{date}, {time}] {name}: {body}'


def run_parse(lines, month_label=None):
    """Write lines to a temp file and run parse_chat on it."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write('\n'.join(lines))
        fname = f.name
    try:
        return parse_chat(fname, month_label)
    finally:
        os.unlink(fname)


# ── _infer_year ───────────────────────────────────────────────────────────────

class TestInferYear(unittest.TestCase):

    def wa(self, year, month, day=15):
        return datetime(year, month, day)

    def test_same_year_when_closer(self):
        # Feb sent in Mar → Feb 2026 (1 month) closer than Feb 2025 (13 months)
        self.assertEqual(_infer_year(2, 14, self.wa(2026, 3)), 2026)

    def test_prev_year_when_closer(self):
        # Dec sent in Mar → Dec 2025 (3 months) closer than Dec 2026 (9 months)
        self.assertEqual(_infer_year(12, 14, self.wa(2026, 3)), 2025)

    def test_nearby_future_month(self):
        # Dec sent in Nov → Dec 2026 (1 month) closer than Dec 2025 (11 months)
        self.assertEqual(_infer_year(12, 14, self.wa(2026, 11)), 2026)

    def test_same_month(self):
        # Same month as message → same year (0 days diff beats 365)
        self.assertEqual(_infer_year(3, 14, self.wa(2026, 3)), 2026)

    def test_jan_sent_in_jan(self):
        self.assertEqual(_infer_year(1, 14, self.wa(2026, 1)), 2026)


# ── extract_date_override ─────────────────────────────────────────────────────

class TestExtractDateOverride(unittest.TestCase):

    WA = '15 Mar 2026'

    # ── No override ──────────────────────────────────────────────────────────

    def test_no_override_returns_none(self):
        d, t = extract_date_override('100 food', self.WA)
        self.assertIsNone(d)
        self.assertEqual(t, '100 food')

    def test_unrecognised_tag_unchanged(self):
        d, t = extract_date_override('100 food {not a date}', self.WA)
        self.assertIsNone(d)
        self.assertIn('{not a date}', t)

    # ── Formats with explicit year ────────────────────────────────────────────

    def test_dd_mm_yy(self):
        d, t = extract_date_override('100 food {14-02-26}', self.WA)
        self.assertEqual(d, '14 Feb 2026')
        self.assertEqual(t, '100 food')

    def test_dd_mm_yyyy(self):
        d, _ = extract_date_override('100 food {14-02-2026}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_slash_mm_slash_yy(self):
        d, _ = extract_date_override('100 food {14/02/26}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_slash_mm_slash_yyyy(self):
        d, _ = extract_date_override('100 food {14/02/2026}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_mon_yyyy(self):
        d, _ = extract_date_override('100 food {14 feb 2026}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_dash_mon_yyyy(self):
        d, _ = extract_date_override('100 food {14-feb-2026}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_mon_yy(self):
        d, _ = extract_date_override('100 food {14 feb 26}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_dash_mon_yy(self):
        d, _ = extract_date_override('100 food {14-feb-26}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_explicit_future_year_respected(self):
        d, _ = extract_date_override('100 food {14-02-2027}', self.WA)
        self.assertEqual(d, '14 Feb 2027')

    # ── Smart year (no year in tag) ───────────────────────────────────────────

    def test_dd_mon_smart_same_year(self):
        # Feb closer in 2026 than 2025
        d, _ = extract_date_override('100 food {14 feb}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_mon_smart_prev_year(self):
        # Dec closer in 2025 than 2026
        d, _ = extract_date_override('100 food {14 dec}', self.WA)
        self.assertEqual(d, '14 Dec 2025')

    def test_dd_mon_nearby_future(self):
        # Dec sent in Nov → Dec 2026 is closer
        d, _ = extract_date_override('100 food {14 dec}', '15 Nov 2026')
        self.assertEqual(d, '14 Dec 2026')

    def test_dd_slash_mm_smart(self):
        d, _ = extract_date_override('100 food {14/02}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    def test_dd_dash_mm_smart(self):
        d, _ = extract_date_override('100 food {14-02}', self.WA)
        self.assertEqual(d, '14 Feb 2026')

    # ── Month-only ────────────────────────────────────────────────────────────

    def test_month_abbr_same_year(self):
        d, t = extract_date_override('100 food {feb}', self.WA)
        self.assertEqual(d, '28 Feb 2026')
        self.assertEqual(t, '100 food')

    def test_month_full_name(self):
        d, _ = extract_date_override('100 food {february}', self.WA)
        self.assertEqual(d, '28 Feb 2026')

    def test_month_abbr_prev_year(self):
        d, _ = extract_date_override('100 food {dec}', self.WA)
        self.assertEqual(d, '28 Dec 2025')

    def test_month_nearby_future(self):
        # Nov sent in Oct → Nov 2026 closer than Nov 2025
        d, _ = extract_date_override('100 food {nov}', '15 Oct 2026')
        self.assertEqual(d, '28 Nov 2026')

    # ── Tag stripping ─────────────────────────────────────────────────────────

    def test_tag_stripped_mid_text_no_double_space(self):
        _, t = extract_date_override('100 food {14 feb} zomato', self.WA)
        self.assertEqual(t, '100 food zomato')


# ── normalise_category ────────────────────────────────────────────────────────

class TestNormaliseCategory(unittest.TestCase):

    def test_user_override_keyword(self):
        self.assertEqual(normalise_category('zomato'), 'FOOD')

    def test_user_override_case_insensitive(self):
        self.assertEqual(normalise_category('Zomato'), 'FOOD')

    def test_exact_enum_lowercase(self):
        self.assertEqual(normalise_category('food'), 'FOOD')

    def test_exact_enum_uppercase(self):
        self.assertEqual(normalise_category('FOOD'), 'FOOD')

    def test_underscore_normalised_hashtag(self):
        self.assertEqual(normalise_category('internaltransfer'), 'TRANSFER_INTERNAL')
        self.assertEqual(normalise_category('externaltransfer'), 'TRANSFER_EXTERNAL')
        self.assertEqual(normalise_category('localtravel'), 'LOCAL_TRAVEL')

    def test_unrecognised_returns_empty(self):
        self.assertEqual(normalise_category('notacategory'), '')

    def test_empty_string(self):
        self.assertEqual(normalise_category(''), '')


# ── extract_category ──────────────────────────────────────────────────────────

class TestExtractCategory(unittest.TestCase):

    def test_hashtag_lowercase(self):
        cat, text = extract_category('zomato #food')
        self.assertEqual(cat, 'FOOD')
        self.assertEqual(text, 'zomato')

    def test_hashtag_uppercase(self):
        cat, text = extract_category('Dior perfume #GROOMING')
        self.assertEqual(cat, 'GROOMING')
        self.assertEqual(text, 'Dior perfume')

    def test_hashtag_shortcut(self):
        cat, _ = extract_category('transfer #internaltransfer')
        self.assertEqual(cat, 'TRANSFER_INTERNAL')

    def test_unrecognised_hashtag_text_unchanged(self):
        cat, text = extract_category('100 food #notreal')
        self.assertEqual(cat, '')
        self.assertIn('#notreal', text)

    def test_no_hashtag(self):
        cat, text = extract_category('100 food')
        self.assertEqual(cat, '')
        self.assertEqual(text, '100 food')


# ── parse_chat (integration) ──────────────────────────────────────────────────

class TestParseChat(unittest.TestCase):

    # ── Basic parsing ─────────────────────────────────────────────────────────

    def test_basic_debit(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '460 zomato')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['amount'], 460.0)
        self.assertEqual(parsed[0]['category'], 'FOOD')
        self.assertEqual(parsed[0]['person'], 'Alice')
        self.assertFalse(parsed[0]['is_credit'])

    def test_basic_credit(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '+50000 salary')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertTrue(parsed[0]['is_credit'])
        self.assertEqual(parsed[0]['category'], 'TRANSFER_EXTERNAL')

    def test_k_multiplier(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '26k rent')], 'feb_2026')
        self.assertEqual(parsed[0]['amount'], 26000.0)

    def test_lakh_multiplier(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '1 lakh mutual funds')], 'feb_2026')
        self.assertEqual(parsed[0]['amount'], 100000.0)

    def test_hashtag_category_override(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '10700 Dior perfume #GROOMING')], 'feb_2026')
        self.assertEqual(parsed[0]['category'], 'GROOMING')
        self.assertEqual(parsed[0]['description'], 'Dior perfume')

    def test_rupee_symbol_stripped(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '₹460 zomato')], 'feb_2026')
        self.assertEqual(parsed[0]['amount'], 460.0)

    def test_amount_only_no_description(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '100')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['amount'], 100.0)
        self.assertEqual(parsed[0]['description'], '')

    def test_decimal_amount_no_description(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '100.00')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['amount'], 100.0)

    def test_indian_comma_format(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '1,00,000 rent')], 'feb_2026')
        self.assertEqual(parsed[0]['amount'], 100000.0)

    def test_western_comma_format(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '100,000 rent')], 'feb_2026')
        self.assertEqual(parsed[0]['amount'], 100000.0)

    def test_comma_format_no_description(self):
        parsed, _ = run_parse([wa_msg('15/02/26', 'Alice', '1,00,000')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['amount'], 100000.0)

    # ── Month filtering ───────────────────────────────────────────────────────

    def test_month_filter_excludes_wrong_month(self):
        lines = [
            wa_msg('15/01/26', 'Alice', '100 food'),
            wa_msg('15/02/26', 'Alice', '200 food'),
        ]
        parsed, _ = run_parse(lines, 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['amount'], 200.0)

    def test_no_month_filter_includes_all(self):
        lines = [
            wa_msg('15/01/26', 'Alice', '100 food'),
            wa_msg('15/02/26', 'Alice', '200 food'),
        ]
        parsed, _ = run_parse(lines)
        self.assertEqual(len(parsed), 2)

    # ── Date override ─────────────────────────────────────────────────────────

    def test_date_override_cross_month(self):
        # March message with Feb override → included in Feb run
        parsed, _ = run_parse([wa_msg('15/03/26', 'Alice', '100 food {14-02-26}')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['date'], '14 Feb 2026')

    def test_date_override_excluded_by_filter(self):
        # March message with March override → excluded from Feb run
        parsed, _ = run_parse([wa_msg('15/03/26', 'Alice', '100 food {14-03-26}')], 'feb_2026')
        self.assertEqual(len(parsed), 0)

    def test_month_only_override(self):
        parsed, _ = run_parse([wa_msg('15/03/26', 'Alice', '100 rent {feb}')], 'feb_2026')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['date'], '28 Feb 2026')

    def test_date_used_in_key(self):
        # Same amount/description but different effective dates → different keys
        lines = [
            wa_msg('15/02/26', 'Alice', '100 food'),
            wa_msg('15/03/26', 'Alice', '100 food {14-02-26}'),
        ]
        parsed, _ = run_parse(lines, 'feb_2026')
        self.assertEqual(len(parsed), 2)
        self.assertNotEqual(parsed[0]['key'], parsed[1]['key'])

    # ── Needs review ──────────────────────────────────────────────────────────

    def test_negative_amount_to_review(self):
        _, unparsed = run_parse([wa_msg('15/02/26', 'Alice', '-500 refund')], 'feb_2026')
        self.assertEqual(len(unparsed), 1)
        self.assertIn('Negative', unparsed[0]['reason'])

    def test_foreign_currency_to_review(self):
        _, unparsed = run_parse([wa_msg('15/02/26', 'Alice', '250 USD hotel')], 'feb_2026')
        self.assertEqual(len(unparsed), 1)
        self.assertIn('Foreign', unparsed[0]['reason'])

    def test_non_numeric_to_review(self):
        _, unparsed = run_parse([wa_msg('15/02/26', 'Alice', 'paid the cab')], 'feb_2026')
        self.assertEqual(len(unparsed), 1)
        self.assertIn('number', unparsed[0]['reason'])

    # ── Ignored messages ──────────────────────────────────────────────────────

    def test_system_encryption_notice_ignored(self):
        lines = [wa_msg('15/02/26', 'Alice', 'Messages and calls are end-to-end encrypted')]
        parsed, unparsed = run_parse(lines, 'feb_2026')
        self.assertEqual(len(parsed) + len(unparsed), 0)

    def test_image_omitted_ignored(self):
        lines = [wa_msg('15/02/26', 'Alice', 'image omitted')]
        parsed, unparsed = run_parse(lines, 'feb_2026')
        self.assertEqual(len(parsed) + len(unparsed), 0)

    def test_deleted_message_ignored(self):
        lines = [wa_msg('15/02/26', 'Alice', 'This message was deleted')]
        parsed, unparsed = run_parse(lines, 'feb_2026')
        self.assertEqual(len(parsed) + len(unparsed), 0)

    # ── Deduplication ─────────────────────────────────────────────────────────

    def test_duplicate_keys_stamped_uniquely(self):
        # Two identical messages → distinct keys via occurrence suffix
        lines = [
            wa_msg('15/02/26', 'Alice', '460 zomato'),
            wa_msg('15/02/26', 'Alice', '460 zomato'),
        ]
        parsed, _ = run_parse(lines, 'feb_2026')
        self.assertEqual(len(parsed), 2)
        self.assertNotEqual(parsed[0]['key'], parsed[1]['key'])
        self.assertTrue(parsed[0]['key'].endswith('_0'))
        self.assertTrue(parsed[1]['key'].endswith('_1'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
