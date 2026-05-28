"""
Scheduled report generation for cron/n8n triggers.

Provides a single entry point that fetches campaign data, generates
reports (PPTX, PDF, HTML), uploads demographics to Google Sheets,
and optionally sends email notifications and Slack alerts.

Designed to be called by n8n cron nodes, system crontab, or
Windows Task Scheduler.

Environment variables (all optional, with sensible defaults):
    LINKEDIN_ACCESS_TOKEN  - LinkedIn API token
    LINKEDIN_ACCOUNT_ID    - LinkedIn ad account ID
    LINKEDIN_CLIENT_ID     - For auto token refresh
    LINKEDIN_CLIENT_SECRET - For auto token refresh
    LINKEDIN_REFRESH_TOKEN - For auto token refresh
    EMAIL_SENDER           - For email notifications
    EMAIL_PASSWORD          - For email notifications
    REPORT_RECIPIENTS      - Comma-separated email addresses
    SLACK_WEBHOOK_URL      - For Slack notifications
    REPORT_MODE            - 'active' (default) or 'all'
    REPORT_OUTPUT_DIR      - Output directory (default: 'output')
"""

import json
import os
import sys
from datetime import datetime


def generate_scheduled_report(mode='active', account_id=None):
    """Generate a complete report on schedule.

    This is the main entry point for automated report generation.
    It performs the following steps:
      1. Refresh LinkedIn access token if needed.
      2. Fetch campaign data (active or all).
      3. Generate PPTX report.
      4. Export PDF (if LibreOffice is available).
      5. Generate HTML report.
      6. Upload demographics to Google Sheets.
      7. Save report data to local SQLite store.
      8. Send email notification (if configured).
      9. Send Slack notification (if configured).

    Args:
        mode: 'active' for active campaigns only, 'all' for all campaigns.
              Falls back to REPORT_MODE env var (default: 'active').
        account_id: LinkedIn ad account ID. Falls back to
                    LINKEDIN_ACCOUNT_ID env var.

    Returns:
        The path to the generated PPTX report, or empty string on failure.
    """
    mode = mode or os.environ.get('REPORT_MODE', 'active')
    account_id = account_id or os.environ.get('LINKEDIN_ACCOUNT_ID', '')
    output_dir = os.environ.get('REPORT_OUTPUT_DIR', 'output')

    # Step 1: Token refresh
    access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN', '')
    try:
        from .token_refresh import auto_refresh_if_needed
        refreshed = auto_refresh_if_needed(access_token=access_token)
        if refreshed:
            access_token = refreshed
        elif not access_token:
            print("Error: No LinkedIn access token available.", file=sys.stderr)
            return ''
    except ImportError:
        if not access_token:
            print("Error: No LinkedIn access token. Set LINKEDIN_ACCESS_TOKEN.",
                  file=sys.stderr)
            return ''

    if not account_id:
        print("Error: No LinkedIn account ID. Set LINKEDIN_ACCOUNT_ID.",
              file=sys.stderr)
        return ''

    # Step 2: Fetch campaign data
    from .linkedin_client import LinkedInClient
    client = LinkedInClient(access_token=access_token, account_id=account_id)

    campaign_filter = 'ACTIVE' if mode.lower() == 'active' else None
    campaigns_list = client.list_campaigns(status_filter=campaign_filter)
    if not campaigns_list:
        print(f"No {mode} campaigns found.", file=sys.stderr)
        return ''

    campaign_ids = [str(c.get('id', c.get('campaignId', ''))) for c in campaigns_list]
    print(f"Scheduled report: {len(campaign_ids)} {mode} campaigns found.",
          file=sys.stderr)

    report_data = client.fetch_all_campaign_data(campaign_ids)
    if not report_data or not report_data.get('campaigns'):
        print("Error: No data returned from LinkedIn API.", file=sys.stderr)
        return ''

    # Prepare output paths
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
    pptx_path = os.path.join(output_dir, f'LinkedIn_Report_{timestamp}.pptx')
    json_path = os.path.join(output_dir, f'LinkedIn_Report_{timestamp}.json')
    pdf_path = os.path.join(output_dir, f'LinkedIn_Report_{timestamp}.pdf')
    html_path = os.path.join(output_dir, f'LinkedIn_Report_{timestamp}.html')

    # Save JSON data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)
    print(f"Data saved: {json_path}", file=sys.stderr)

    # Step 3: Generate PPTX
    pptx_result = ''
    try:
        from .report_generator import generate_report
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(project_dir, 'assets', 'logo.png')
        generate_report(json_path, pptx_path, logo_path=logo_path)
        pptx_result = pptx_path
        print(f"PPTX report: {pptx_path}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: PPTX generation failed: {e}", file=sys.stderr)

    # Step 4: Export PDF
    pdf_result = ''
    try:
        from .pdf_exporter import export_pdf
        pdf_result = export_pdf(pptx_path, pdf_path)
    except Exception as e:
        print(f"Warning: PDF export failed: {e}", file=sys.stderr)

    # Step 5: Generate HTML
    html_result = ''
    try:
        from .html_report import generate_html_report
        html_result = generate_html_report(report_data, output_path=html_path)
    except Exception as e:
        print(f"Warning: HTML report failed: {e}", file=sys.stderr)

    # Step 6: Upload to Google Sheets
    sheet_url = ''
    try:
        from .sheets_uploader import upload_to_sheets
        csv_dir = os.path.join(output_dir, f'demographics_{timestamp}')
        # Check if demographics CSVs were generated
        if os.path.isdir(csv_dir):
            sheet_url = upload_to_sheets(csv_dir, report_data.get('report_date', ''))
    except Exception as e:
        print(f"Warning: Google Sheets upload failed: {e}", file=sys.stderr)

    # Step 7: Save to data store
    try:
        from .data_store import DataStore
        store = DataStore()
        store.save_report(report_data)
    except Exception as e:
        print(f"Warning: Data store save failed: {e}", file=sys.stderr)

    # Step 8: Email notification
    recipients_raw = os.environ.get('REPORT_RECIPIENTS', '')
    if recipients_raw:
        try:
            from .email_sender import send_report_email, format_report_email_body
            recipients = [r.strip() for r in recipients_raw.split(',') if r.strip()]
            body = format_report_email_body(report_data)
            attachments = [p for p in [pptx_result, pdf_result] if p]
            send_report_email(
                recipient_emails=recipients,
                subject=f"LinkedIn Campaign Report - {report_data.get('report_date', '')}",
                body_html=body,
                attachment_paths=attachments,
            )
        except Exception as e:
            print(f"Warning: Email notification failed: {e}", file=sys.stderr)

    # Step 9: Slack notification
    slack_url = os.environ.get('SLACK_WEBHOOK_URL', '')
    if slack_url:
        try:
            from .slack_notifier import send_slack_notification
            send_slack_notification(
                report_data=report_data,
                sheet_url=sheet_url,
            )
        except Exception as e:
            print(f"Warning: Slack notification failed: {e}", file=sys.stderr)

    print(f"Scheduled report complete: {pptx_result}", file=sys.stderr)
    return pptx_result


if __name__ == '__main__':
    # Allow running directly: python -m src.scheduled_report [mode]
    import argparse
    parser = argparse.ArgumentParser(description='Generate scheduled LinkedIn report')
    parser.add_argument('--mode', default='active', choices=['active', 'all'],
                        help='Campaign filter mode (default: active)')
    parser.add_argument('--account-id', default=None,
                        help='LinkedIn ad account ID (or LINKEDIN_ACCOUNT_ID env)')
    args = parser.parse_args()

    result = generate_scheduled_report(mode=args.mode, account_id=args.account_id)
    if result:
        print(result)
    else:
        sys.exit(1)
