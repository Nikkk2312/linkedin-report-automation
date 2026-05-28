"""Unit tests for src/formatters.py"""

import unittest
from src.formatters import (
    format_number, format_ctr, calc_ctr_value, format_currency,
    abbreviate_number, format_percentage, format_date_ordinal,
)


class TestFormatNumber(unittest.TestCase):
    """Tests for format_number()."""

    def test_zero(self):
        self.assertEqual(format_number(0), '0')

    def test_thousand(self):
        self.assertEqual(format_number(1000), '1,000')

    def test_million(self):
        self.assertEqual(format_number(1000000), '1,000,000')

    def test_none(self):
        self.assertEqual(format_number(None), 'NA')

    def test_na_string(self):
        self.assertEqual(format_number('NA'), 'NA')

    def test_string_number(self):
        self.assertEqual(format_number('5000'), '5,000')

    def test_negative(self):
        self.assertEqual(format_number(-1500), '-1,500')

    def test_float_truncated(self):
        self.assertEqual(format_number(1234.7), '1,234')

    def test_invalid_string(self):
        self.assertEqual(format_number('abc'), 'abc')


class TestFormatCtr(unittest.TestCase):
    """Tests for format_ctr()."""

    def test_normal(self):
        self.assertEqual(format_ctr(10000, 150), '1.50%')

    def test_zero_impressions(self):
        self.assertEqual(format_ctr(0, 100), 'NA')

    def test_none_impressions(self):
        self.assertEqual(format_ctr(None, 100), 'NA')

    def test_none_clicks(self):
        self.assertEqual(format_ctr(1000, None), 'NA')

    def test_both_none(self):
        self.assertEqual(format_ctr(None, None), 'NA')

    def test_string_inputs(self):
        self.assertEqual(format_ctr('10000', '200'), '2.00%')


class TestCalcCtrValue(unittest.TestCase):
    """Tests for calc_ctr_value()."""

    def test_normal(self):
        result = calc_ctr_value(10000, 150)
        self.assertAlmostEqual(result, 1.5)

    def test_zero_impressions(self):
        self.assertIsNone(calc_ctr_value(0, 100))

    def test_none_impressions(self):
        self.assertIsNone(calc_ctr_value(None, 100))

    def test_none_clicks(self):
        self.assertIsNone(calc_ctr_value(1000, None))

    def test_both_none(self):
        self.assertIsNone(calc_ctr_value(None, None))

    def test_high_ctr(self):
        result = calc_ctr_value(100, 50)
        self.assertAlmostEqual(result, 50.0)


class TestFormatCurrency(unittest.TestCase):
    """Tests for format_currency()."""

    def test_usd(self):
        self.assertEqual(format_currency(1234.56), '$1,234.56')

    def test_eur(self):
        self.assertEqual(format_currency(99.9, 'EUR'), '\u20ac99.90')

    def test_inr(self):
        self.assertEqual(format_currency(500, 'INR'), '\u20b9500.00')

    def test_none(self):
        self.assertEqual(format_currency(None), 'NA')

    def test_unknown_currency(self):
        result = format_currency(100, 'JPY')
        self.assertEqual(result, 'JPY 100.00')

    def test_zero(self):
        self.assertEqual(format_currency(0), '$0.00')

    def test_string_input(self):
        self.assertEqual(format_currency('42.5'), '$42.50')


class TestAbbreviateNumber(unittest.TestCase):
    """Tests for abbreviate_number()."""

    def test_million(self):
        self.assertEqual(abbreviate_number(1234567), '1.2M')

    def test_thousand(self):
        self.assertEqual(abbreviate_number(45000), '45.0K')

    def test_small_number(self):
        self.assertEqual(abbreviate_number(999), '999')

    def test_none(self):
        self.assertEqual(abbreviate_number(None), 'NA')

    def test_exact_million(self):
        self.assertEqual(abbreviate_number(1000000), '1.0M')

    def test_exact_thousand(self):
        self.assertEqual(abbreviate_number(1000), '1.0K')

    def test_zero(self):
        self.assertEqual(abbreviate_number(0), '0')

    def test_invalid_string(self):
        self.assertEqual(abbreviate_number('abc'), 'abc')


class TestFormatPercentage(unittest.TestCase):
    """Tests for format_percentage()."""

    def test_normal(self):
        self.assertEqual(format_percentage(3.456), '3.5%')

    def test_none(self):
        self.assertEqual(format_percentage(None), 'NA')

    def test_custom_decimals(self):
        self.assertEqual(format_percentage(3.456, decimals=2), '3.46%')

    def test_zero(self):
        self.assertEqual(format_percentage(0.0), '0.0%')

    def test_large_value(self):
        self.assertEqual(format_percentage(100.0, decimals=0), '100%')


class TestFormatDateOrdinal(unittest.TestCase):
    """Tests for format_date_ordinal()."""

    def test_normal_date(self):
        self.assertEqual(format_date_ordinal('2025-12-08'), '8th Dec 2025')

    def test_1st(self):
        self.assertEqual(format_date_ordinal('2025-01-01'), '1st Jan 2025')

    def test_2nd(self):
        self.assertEqual(format_date_ordinal('2025-03-02'), '2nd Mar 2025')

    def test_3rd(self):
        self.assertEqual(format_date_ordinal('2025-06-03'), '3rd Jun 2025')

    def test_11th(self):
        self.assertEqual(format_date_ordinal('2025-07-11'), '11th Jul 2025')

    def test_12th(self):
        self.assertEqual(format_date_ordinal('2025-07-12'), '12th Jul 2025')

    def test_13th(self):
        self.assertEqual(format_date_ordinal('2025-07-13'), '13th Jul 2025')

    def test_21st(self):
        self.assertEqual(format_date_ordinal('2025-05-21'), '21st May 2025')

    def test_none(self):
        self.assertEqual(format_date_ordinal(None), 'NA')

    def test_invalid_string(self):
        self.assertEqual(format_date_ordinal('not-a-date'), 'not-a-date')

    def test_empty_string(self):
        self.assertEqual(format_date_ordinal(''), 'NA')


if __name__ == '__main__':
    unittest.main()
