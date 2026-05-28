"""Unit tests for src/config.py"""

import unittest
from pptx.dml.color import RGBColor

from src.config import (
    get_theme, THEME_LINKEDIN, THEME_DARK, THEME_CORPORATE,
    CLR_LINKEDIN_BLUE, CLR_ACCENT_DARK, CLR_ORANGE, CLR_BLACK, CLR_WHITE,
    CLR_ROW_LIGHT, CLR_BORDER, CLR_DARK_GRAY, CLR_SUBTLE_GRAY,
    CLR_LIGHT_GRAY, CLR_SUCCESS_GREEN, CLR_DANGER_RED,
    CTR_BENCHMARKS,
)

REQUIRED_THEME_KEYS = {'primary', 'accent', 'success', 'danger', 'bg', 'text'}


class TestGetTheme(unittest.TestCase):
    """Tests for get_theme()."""

    def test_default_returns_dict(self):
        theme = get_theme('linkedin')
        self.assertIsInstance(theme, dict)

    def test_linkedin_theme(self):
        theme = get_theme('linkedin')
        self.assertEqual(theme, THEME_LINKEDIN)

    def test_dark_theme(self):
        theme = get_theme('dark')
        self.assertEqual(theme, THEME_DARK)

    def test_corporate_theme(self):
        theme = get_theme('corporate')
        self.assertEqual(theme, THEME_CORPORATE)

    def test_unknown_theme_falls_back(self):
        theme = get_theme('nonexistent')
        self.assertEqual(theme, THEME_LINKEDIN)

    def test_case_insensitive(self):
        theme = get_theme('DARK')
        self.assertEqual(theme, THEME_DARK)


class TestThemeKeys(unittest.TestCase):
    """Ensure all themes have the required keys."""

    def test_linkedin_has_required_keys(self):
        self.assertTrue(REQUIRED_THEME_KEYS.issubset(THEME_LINKEDIN.keys()))

    def test_dark_has_required_keys(self):
        self.assertTrue(REQUIRED_THEME_KEYS.issubset(THEME_DARK.keys()))

    def test_corporate_has_required_keys(self):
        self.assertTrue(REQUIRED_THEME_KEYS.issubset(THEME_CORPORATE.keys()))

    def test_theme_values_are_tuples(self):
        for name, theme in [('linkedin', THEME_LINKEDIN), ('dark', THEME_DARK), ('corporate', THEME_CORPORATE)]:
            for key in REQUIRED_THEME_KEYS:
                self.assertIsInstance(theme[key], tuple, f"{name}.{key} should be a tuple")
                self.assertEqual(len(theme[key]), 3, f"{name}.{key} should have 3 elements (R, G, B)")


class TestColorConstants(unittest.TestCase):
    """Verify color constants are RGBColor instances."""

    def test_clr_linkedin_blue(self):
        self.assertIsInstance(CLR_LINKEDIN_BLUE, RGBColor)

    def test_clr_accent_dark(self):
        self.assertIsInstance(CLR_ACCENT_DARK, RGBColor)

    def test_clr_orange(self):
        self.assertIsInstance(CLR_ORANGE, RGBColor)

    def test_clr_black(self):
        self.assertIsInstance(CLR_BLACK, RGBColor)

    def test_clr_white(self):
        self.assertIsInstance(CLR_WHITE, RGBColor)

    def test_clr_row_light(self):
        self.assertIsInstance(CLR_ROW_LIGHT, RGBColor)

    def test_clr_border(self):
        self.assertIsInstance(CLR_BORDER, RGBColor)

    def test_clr_dark_gray(self):
        self.assertIsInstance(CLR_DARK_GRAY, RGBColor)

    def test_clr_subtle_gray(self):
        self.assertIsInstance(CLR_SUBTLE_GRAY, RGBColor)

    def test_clr_light_gray(self):
        self.assertIsInstance(CLR_LIGHT_GRAY, RGBColor)

    def test_clr_success_green(self):
        self.assertIsInstance(CLR_SUCCESS_GREEN, RGBColor)

    def test_clr_danger_red(self):
        self.assertIsInstance(CLR_DANGER_RED, RGBColor)


class TestCtrBenchmarks(unittest.TestCase):
    """Tests for CTR_BENCHMARKS dict."""

    def test_has_default_key(self):
        self.assertIn('default', CTR_BENCHMARKS)

    def test_has_engagement_key(self):
        self.assertIn('Engagement', CTR_BENCHMARKS)

    def test_has_brand_awareness_key(self):
        self.assertIn('Brand Awareness', CTR_BENCHMARKS)

    def test_has_website_visits_key(self):
        self.assertIn('Website Visits', CTR_BENCHMARKS)

    def test_has_lead_generation_key(self):
        self.assertIn('Lead Generation', CTR_BENCHMARKS)

    def test_values_are_floats(self):
        for key, val in CTR_BENCHMARKS.items():
            self.assertIsInstance(val, float, f"CTR_BENCHMARKS['{key}'] should be a float")

    def test_values_are_positive(self):
        for key, val in CTR_BENCHMARKS.items():
            self.assertGreater(val, 0, f"CTR_BENCHMARKS['{key}'] should be positive")


if __name__ == '__main__':
    unittest.main()
