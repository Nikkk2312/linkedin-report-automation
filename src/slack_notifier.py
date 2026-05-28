"""
Send report notifications to Slack channels via incoming webhooks.

Formats a rich Slack message with blocks showing key campaign metrics,
top performer, and action links.

Environment variables:
    SLACK_WEBHOOK_URL - Slack incoming webhook URL
"""

import json
import os
import sys

import requests


def _build_slack_blocks(report_data, report_url='', sheet_url=''):
    """Build Slack Block Kit blocks for a report notification.

    Args:
        report_data: Dict with 'campaigns' list and 'report_date' string.
        report_url: Optional URL to download the report file.
        sheet_url: Optional Google Sheets URL.

    Returns:
        List of Slack block dicts.
    """
    campaigns = report_data.get('campaigns', [])
    report_date = report_data.get('report_date', 'N/A')

    # Aggregate totals
    total_impressions = 0
    total_clicks = 0
    total_engagements = 0
    total_spend = 0.0
    for c in campaigns:
        total_impressions += c.get('impressions') or 0
        total_clicks += c.get('clicks') or 0
        total_engagements += c.get('engagements') or 0
        total_spend += c.get('cost_usd') or 0.0

    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0

    # Find top campaign by CTR (with minimum impressions threshold)
    top_campaign = 'N/A'
    top_ctr = 0
    for c in campaigns:
        imp = c.get('impressions') or 0
        ctr = c.get('ctr') or 0
        if imp >= 100 and ctr > top_ctr:
            top_ctr = ctr
            top_campaign = c.get('display_name', c.get('name', 'N/A'))

    # If no campaign met the threshold, pick by impressions
    if top_campaign == 'N/A' and campaigns:
        top = max(campaigns, key=lambda c: c.get('impressions') or 0)
        top_campaign = top.get('display_name', top.get('name', 'N/A'))
        top_ctr = top.get('ctr') or 0

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "LinkedIn Report Generated",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Report Date:* {report_date}",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Impressions:*\n{total_impressions:,}"},
                {"type": "mrkdwn", "text": f"*Clicks:*\n{total_clicks:,}"},
                {"type": "mrkdwn", "text": f"*CTR:*\n{overall_ctr:.2f}%"},
                {"type": "mrkdwn", "text": f"*Spend:*\n${total_spend:,.2f}"},
            ],
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Campaigns:*\n{len(campaigns)}"},
                {"type": "mrkdwn", "text": f"*Top Performer:*\n{top_campaign} ({top_ctr:.2f}% CTR)"},
            ],
        },
        {"type": "divider"},
    ]

    # Action buttons
    action_elements = []
    if report_url:
        action_elements.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "Download Report"},
            "url": report_url,
            "style": "primary",
        })
    if sheet_url:
        action_elements.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "Open Google Sheets"},
            "url": sheet_url,
        })

    if action_elements:
        blocks.append({
            "type": "actions",
            "elements": action_elements,
        })

    return blocks


def send_slack_notification(
    report_data,
    report_url='',
    sheet_url='',
    webhook_url=None,
):
    """Send a report notification to a Slack channel via webhook.

    Args:
        report_data: Dict with 'campaigns' list and 'report_date' string,
                     as returned by LinkedInClient.fetch_all_campaign_data().
        report_url: Optional URL to download the report file.
        sheet_url: Optional Google Sheets URL with demographics data.
        webhook_url: Slack incoming webhook URL. Falls back to
                     SLACK_WEBHOOK_URL env var.

    Returns:
        True on success, False on failure.
    """
    webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK_URL', '')

    if not webhook_url:
        print("  Warning: Slack webhook URL not configured. "
              "Set SLACK_WEBHOOK_URL.", file=sys.stderr)
        return False

    try:
        blocks = _build_slack_blocks(report_data, report_url, sheet_url)
        payload = {
            "text": "LinkedIn Campaign Report Generated",
            "blocks": blocks,
        }

        resp = requests.post(
            webhook_url,
            json=payload,
            timeout=15,
        )

        if resp.status_code == 200 and resp.text == 'ok':
            print("  Slack notification sent.", file=sys.stderr)
            return True
        else:
            print(f"  Warning: Slack webhook returned {resp.status_code}: {resp.text}",
                  file=sys.stderr)
            return False

    except requests.exceptions.Timeout:
        print("  Warning: Slack webhook request timed out.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Warning: Slack notification failed: {e}", file=sys.stderr)
        return False
