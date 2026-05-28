"""Number and date formatting utilities."""

from datetime import datetime
from typing import Optional, Union


def format_number(n: Optional[Union[int, float, str]]) -> str:
    """Format number with commas. Returns 'NA' for None."""
    if n is None or n == 'NA':
        return 'NA'
    try:
        return f'{int(n):,}'
    except (ValueError, TypeError):
        return str(n)


def format_ctr(impressions: Optional[Union[int, float]], clicks: Optional[Union[int, float]]) -> str:
    """Calculate and format CTR as percentage."""
    if impressions is None or clicks is None or impressions == 0:
        return 'NA'
    try:
        ctr = (int(clicks) / int(impressions)) * 100
        return f'{ctr:.2f}%'
    except (ValueError, TypeError, ZeroDivisionError):
        return 'NA'


def calc_ctr_value(impressions: Optional[Union[int, float]], clicks: Optional[Union[int, float]]) -> Optional[float]:
    """Calculate CTR as a float. Returns None if not calculable."""
    if impressions is None or clicks is None or impressions == 0:
        return None
    try:
        return (int(clicks) / int(impressions)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def format_date_ordinal(date_str: Optional[str]) -> str:
    """Convert date to format like '8th Dec 2025'."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        day = dt.day
        if 11 <= day <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return f'{day}{suffix} {dt.strftime("%b %Y")}'
    except (ValueError, TypeError):
        return str(date_str) if date_str else 'NA'


def format_percentage(value: Optional[float], decimals: int = 1) -> str:
    """Format a float as percentage string."""
    if value is None:
        return 'NA'
    return f'{value:.{decimals}f}%'


def format_currency(amount: Optional[Union[int, float, str]], currency: str = 'USD') -> str:
    """Format amount as currency."""
    if amount is None:
        return 'NA'
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹'}
    symbol = symbols.get(currency, currency + ' ')
    try:
        return f'{symbol}{float(amount):,.2f}'
    except (ValueError, TypeError):
        return str(amount)


def abbreviate_number(n: Optional[Union[int, float, str]]) -> str:
    """Abbreviate large numbers: 1,234,567 -> 1.2M."""
    if n is None:
        return 'NA'
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 1_000_000:
        return f'{n / 1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n / 1_000:.1f}K'
    return str(n)
