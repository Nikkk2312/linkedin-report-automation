"""
Notify external systems when reports are ready.

POSTs report metadata to a callback URL with retry logic.
Supports custom headers via the WEBHOOK_CALLBACK_HEADERS env var
(JSON-encoded dict).

Environment variables:
    WEBHOOK_CALLBACK_URL     - Default callback URL
    WEBHOOK_CALLBACK_HEADERS - JSON string of custom headers, e.g.
                               '{"X-Api-Key": "abc123"}'
"""

import json
import os
import sys
import time

import requests


DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2  # seconds


def _parse_custom_headers():
    """Parse custom headers from the WEBHOOK_CALLBACK_HEADERS env var.

    Returns:
        Dict of header name/value pairs, or empty dict.
    """
    raw = os.environ.get('WEBHOOK_CALLBACK_HEADERS', '')
    if not raw:
        return {}
    try:
        headers = json.loads(raw)
        if isinstance(headers, dict):
            return headers
    except (json.JSONDecodeError, TypeError):
        print("  Warning: WEBHOOK_CALLBACK_HEADERS is not valid JSON. Ignoring.",
              file=sys.stderr)
    return {}


def _build_payload(report_data, report_path='', sheet_url=''):
    """Build the webhook payload from report data.

    Args:
        report_data: Dict with 'campaigns' list and 'report_date'.
        report_path: Local path or URL to the report file.
        sheet_url: Google Sheets URL.

    Returns:
        Dict payload for the webhook POST body.
    """
    campaigns = report_data.get('campaigns', [])

    total_impressions = sum(c.get('impressions') or 0 for c in campaigns)
    total_clicks = sum(c.get('clicks') or 0 for c in campaigns)
    total_spend = sum(c.get('cost_usd') or 0.0 for c in campaigns)
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0

    payload = {
        'event': 'report_generated',
        'report_date': report_data.get('report_date', ''),
        'campaign_count': len(campaigns),
        'metrics': {
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_spend': round(total_spend, 2),
            'overall_ctr': round(overall_ctr, 2),
        },
        'campaigns': [
            {
                'id': c.get('id', ''),
                'name': c.get('display_name', c.get('name', '')),
                'impressions': c.get('impressions') or 0,
                'clicks': c.get('clicks') or 0,
                'ctr': round(c.get('ctr') or 0, 2),
                'spend': round(c.get('cost_usd') or 0, 2),
            }
            for c in campaigns
        ],
    }

    if report_path:
        payload['report_path'] = report_path
    if sheet_url:
        payload['sheet_url'] = sheet_url

    return payload


def notify_webhook(callback_url, report_data, report_path='', sheet_url='',
                   max_retries=DEFAULT_MAX_RETRIES):
    """POST report metadata to a callback URL with retry logic.

    Args:
        callback_url: The URL to POST the report metadata to.
        report_data: Dict with 'campaigns' list and 'report_date' string,
                     as returned by LinkedInClient.fetch_all_campaign_data().
        report_path: Local path or URL to the generated report file.
        sheet_url: Google Sheets URL with demographics data.
        max_retries: Number of retry attempts (default: 3).

    Returns:
        True on success (HTTP 2xx), False on failure.
    """
    if not callback_url:
        callback_url = os.environ.get('WEBHOOK_CALLBACK_URL', '')
    if not callback_url:
        print("  Warning: No webhook callback URL provided.", file=sys.stderr)
        return False

    payload = _build_payload(report_data, report_path, sheet_url)
    custom_headers = _parse_custom_headers()

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'LinkedIn-Report-Automation/1.0',
    }
    headers.update(custom_headers)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                callback_url,
                json=payload,
                headers=headers,
                timeout=15,
            )
            if 200 <= resp.status_code < 300:
                print(f"  Webhook callback sent to {callback_url} "
                      f"(HTTP {resp.status_code}).", file=sys.stderr)
                return True
            else:
                last_error = f'HTTP {resp.status_code}: {resp.text[:200]}'
                print(f"  Warning: Webhook attempt {attempt}/{max_retries} "
                      f"failed: {last_error}", file=sys.stderr)

        except requests.exceptions.Timeout:
            last_error = 'Request timed out'
            print(f"  Warning: Webhook attempt {attempt}/{max_retries} "
                  f"timed out.", file=sys.stderr)
        except requests.exceptions.ConnectionError as e:
            last_error = f'Connection error: {e}'
            print(f"  Warning: Webhook attempt {attempt}/{max_retries} "
                  f"connection failed.", file=sys.stderr)
        except Exception as e:
            last_error = str(e)
            print(f"  Warning: Webhook attempt {attempt}/{max_retries} "
                  f"failed: {e}", file=sys.stderr)

        if attempt < max_retries:
            delay = DEFAULT_RETRY_DELAY * attempt
            time.sleep(delay)

    print(f"  Warning: Webhook callback failed after {max_retries} attempts. "
          f"Last error: {last_error}", file=sys.stderr)
    return False
