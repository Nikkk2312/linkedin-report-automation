"""Configuration and color constants for report generation."""

import os
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor


# ─── BRANDING ─────────────────────────────────────────────────────────────────
BRAND_NAME = os.getenv('BRAND_NAME', 'LinkedIn Report Automation')
BRAND_TAGLINE = os.getenv('BRAND_TAGLINE', 'Automated Ad Campaign Reporting')
COMPANY_NAME = os.getenv('COMPANY_NAME', '')
CUSTOM_FOOTER = os.getenv('REPORT_FOOTER', 'Generated with LinkedIn Report Automation')
SLIDE_FOOTER_ENABLED = os.getenv('SLIDE_FOOTER_ENABLED', 'true').lower() == 'true'

# ─── AI INSIGHTS ──────────────────────────────────────────────────────────────
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')

# ─── DELIVERY CHANNELS ───────────────────────────────────────────────────────
EMAIL_ENABLED = os.getenv('EMAIL_DELIVERY', 'false').lower() == 'true'
SLACK_ENABLED = os.getenv('SLACK_NOTIFICATIONS', 'false').lower() == 'true'

# ─── DATA STORAGE ────────────────────────────────────────────────────────────
DATA_STORE_PATH = os.getenv('DATA_STORE_PATH', 'data/reports.db')
ARCHIVE_MAX_DAYS = int(os.getenv('REPORT_ARCHIVE_DAYS', '30'))

# ─── WEBHOOK ─────────────────────────────────────────────────────────────────
WEBHOOK_API_KEY = os.getenv('WEBHOOK_API_KEY', '')

# ─── SLIDE DIMENSIONS ─────────────────────────────────────────────────────────
SLIDE_WIDTH = Emu(9144000)   # 10 inches
SLIDE_HEIGHT = Emu(6858000)  # 7.5 inches

# ─── COLOR THEME PRESETS ──────────────────────────────────────────────────────
THEME_LINKEDIN = {
    'primary':   (0x0A, 0x66, 0xC2),  # LinkedIn Blue
    'accent':    (0x00, 0x4B, 0x87),  # Accent Dark
    'success':   (0x05, 0x7A, 0x42),  # Green
    'danger':    (0xCC, 0x1C, 0x39),  # Red
    'bg':        (0xF8, 0xF9, 0xFA),  # Light Gray background
    'text':      (0x33, 0x33, 0x33),  # Dark Gray text
}

THEME_DARK = {
    'primary':   (0x1A, 0x1A, 0x2E),  # Deep Navy
    'accent':    (0x16, 0x21, 0x3E),  # Dark Blue
    'success':   (0x00, 0xD2, 0x7A),  # Bright Green
    'danger':    (0xE7, 0x4C, 0x3C),  # Bright Red
    'bg':        (0x0F, 0x0F, 0x1A),  # Near Black
    'text':      (0xE0, 0xE0, 0xE0),  # Light Gray text
}

THEME_CORPORATE = {
    'primary':   (0x2C, 0x3E, 0x50),  # Charcoal
    'accent':    (0x34, 0x49, 0x5E),  # Wet Asphalt
    'success':   (0x27, 0xAE, 0x60),  # Emerald
    'danger':    (0xC0, 0x39, 0x2B),  # Pomegranate
    'bg':        (0xFC, 0xFC, 0xFC),  # Near White
    'text':      (0x2C, 0x3E, 0x50),  # Charcoal text
}

_THEMES = {
    'linkedin': THEME_LINKEDIN,
    'dark': THEME_DARK,
    'corporate': THEME_CORPORATE,
}


def get_theme(name: str = None) -> dict:
    """Return a theme dict by name. Falls back to linkedin theme."""
    if name is None:
        name = os.getenv('THEME', 'linkedin')
    return _THEMES.get(name.lower(), THEME_LINKEDIN)


# ─── COLOR PALETTE — LinkedIn-inspired professional theme ──────────────────────
# These remain the active colors used throughout the codebase.
CLR_LINKEDIN_BLUE = RGBColor(0x0A, 0x66, 0xC2)
CLR_ACCENT_DARK = RGBColor(0x00, 0x4B, 0x87)
CLR_ORANGE = RGBColor(0xF5, 0xA6, 0x23)
CLR_BLACK = RGBColor(0x00, 0x00, 0x00)
CLR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CLR_ROW_LIGHT = RGBColor(0xEE, 0xF3, 0xF8)
CLR_BORDER = RGBColor(0xD0, 0xD5, 0xDD)
CLR_DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
CLR_SUBTLE_GRAY = RGBColor(0x66, 0x66, 0x66)
CLR_LIGHT_GRAY = RGBColor(0xF8, 0xF9, 0xFA)
CLR_SUCCESS_GREEN = RGBColor(0x05, 0x7A, 0x42)
CLR_DANGER_RED = RGBColor(0xCC, 0x1C, 0x39)

# ─── LOGO POSITION ────────────────────────────────────────────────────────────
LOGO_LEFT = Emu(7841518)
LOGO_TOP = Emu(103237)
LOGO_WIDTH = Emu(1135281)
LOGO_HEIGHT = Emu(368031)

# ─── TYPOGRAPHY ────────────────────────────────────────────────────────────────
FONT_NAME = 'Calibri'
FONT_SIZE_TITLE = Pt(36)
FONT_SIZE_HEADING = Pt(28)
FONT_SIZE_SUBHEADING = Pt(20)
FONT_SIZE_BODY = Pt(13)
FONT_SIZE_SMALL = Pt(10)
FONT_SIZE_CAPTION = Pt(9)

# ─── CAMPAIGN TYPE DISPLAY NAMES ──────────────────────────────────────────────
CAMPAIGN_TYPES = {
    'ENGAGEMENT': 'Engagement',
    'BRAND_AWARENESS': 'Brand Awareness',
    'WEBSITE_VISIT': 'Website Visits',
    'LEAD_GENERATION': 'Lead Generation',
    'JOB_APPLICANT': 'Job Applicants',
    'VIDEO_VIEWS': 'Video Views',
    'WEBSITE_CONVERSIONS': 'Website Conversions',
}

# ─── CTR BENCHMARKS (LinkedIn average by campaign type) ────────────────────────
CTR_BENCHMARKS = {
    'Engagement': 0.50,
    'Brand Awareness': 0.40,
    'Website Visits': 0.65,
    'Lead Generation': 0.50,
    'Video Views': 0.45,
    'default': 0.44,
}

# ─── 2026 LINKEDIN BENCHMARKS BY FORMAT ──────────────────────────────────────
BENCHMARKS_2026 = {
    'ctr': {
        'single_image': 0.56,
        'carousel': 0.40,
        'video': 0.44,
        'message': 3.0,
        'document': 0.43,
        'event': 0.55,
        'overall': 0.56,
    },
    'cpc': {
        'accounting': 5.00,
        'business_development': 6.30,
        'engineering': 5.10,
        'finance': 6.90,
        'information_technology': 7.90,
        'marketing': 6.80,
        'sales': 5.40,
        'overall': 5.58,
    },
    'cpm': {
        'overall': 33.80,
    },
    'engagement_rate': {
        'non_video': 0.5,
        'video': 1.6,
        'overall': 0.5,
    },
    'video_view_through_rate': 29.5,
    'lead_form_completion_rate': 10.0,
    'conversion_rate': 6.1,
    'cost_per_lead': {
        'namer': 230,
        'apac': 80,
        'emea': 120,
        'latam': 60,
        'overall': 120,
    },
}

# ─── OLLAMA / AI CONFIG ──────────────────────────────────────────────────────
OLLAMA_ENABLED = os.getenv('OLLAMA_ENABLED', 'true').lower() == 'true'
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
AI_INSIGHTS_ENABLED = os.getenv('AI_INSIGHTS_ENABLED', 'true').lower() == 'true'
