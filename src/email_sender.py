"""
Send reports via email using Gmail SMTP or generic SMTP.

Supports attaching PPTX and PDF report files, and generates
an HTML email body with a metrics summary table.

Environment variables:
    EMAIL_SMTP_HOST   - SMTP server (default: smtp.gmail.com)
    EMAIL_SMTP_PORT   - SMTP port (default: 587)
    EMAIL_SENDER      - Sender email address
    EMAIL_PASSWORD    - Sender password or Gmail app password
"""

import os
import ssl
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


def format_report_email_body(report_data):
    """Generate an HTML email body with a metrics summary table.

    Args:
        report_data: Dict with 'campaigns' list and 'report_date' string,
                     as returned by LinkedInClient.fetch_all_campaign_data().

    Returns:
        HTML string suitable for an email body.
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
    overall_cpc = (total_spend / total_clicks) if total_clicks else 0

    # Find top campaign by impressions
    top_campaign = 'N/A'
    if campaigns:
        top = max(campaigns, key=lambda c: c.get('impressions') or 0)
        top_campaign = top.get('display_name', top.get('name', 'N/A'))

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Calibri, Arial, sans-serif; color: #333; max-width: 640px; margin: 0 auto;">
  <div style="background: #0A66C2; padding: 20px 24px; border-radius: 8px 8px 0 0;">
    <h1 style="color: #fff; margin: 0; font-size: 22px;">LinkedIn Campaign Report</h1>
    <p style="color: #ddd; margin: 4px 0 0; font-size: 14px;">Report Date: {report_date}</p>
  </div>

  <div style="padding: 20px 24px; border: 1px solid #ddd; border-top: none;">
    <h2 style="font-size: 16px; color: #0A66C2; margin-top: 0;">Executive Summary</h2>
    <p style="font-size: 14px;">
      This report covers <strong>{len(campaigns)}</strong> campaign(s) with a total spend
      of <strong>${total_spend:,.2f}</strong>.
    </p>

    <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin: 16px 0;">
      <tr style="background: #0A66C2; color: #fff;">
        <th style="padding: 8px 12px; text-align: left;">Metric</th>
        <th style="padding: 8px 12px; text-align: right;">Value</th>
      </tr>
      <tr style="background: #f8f9fa;">
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">Campaigns</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">{len(campaigns)}</td>
      </tr>
      <tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">Impressions</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">{total_impressions:,}</td>
      </tr>
      <tr style="background: #f8f9fa;">
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">Clicks</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">{total_clicks:,}</td>
      </tr>
      <tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">CTR</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">{overall_ctr:.2f}%</td>
      </tr>
      <tr style="background: #f8f9fa;">
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">Engagements</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">{total_engagements:,}</td>
      </tr>
      <tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">Total Spend</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">${total_spend:,.2f}</td>
      </tr>
      <tr style="background: #f8f9fa;">
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd;">Avg CPC</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #ddd; text-align: right;">${overall_cpc:,.2f}</td>
      </tr>
      <tr>
        <td style="padding: 8px 12px;">Top Campaign</td>
        <td style="padding: 8px 12px; text-align: right;">{top_campaign}</td>
      </tr>
    </table>

    <h2 style="font-size: 16px; color: #0A66C2;">Campaign Breakdown</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin: 12px 0;">
      <tr style="background: #004B87; color: #fff;">
        <th style="padding: 6px 10px; text-align: left;">Campaign</th>
        <th style="padding: 6px 10px; text-align: right;">Impr.</th>
        <th style="padding: 6px 10px; text-align: right;">Clicks</th>
        <th style="padding: 6px 10px; text-align: right;">CTR</th>
        <th style="padding: 6px 10px; text-align: right;">Spend</th>
      </tr>"""

    for i, c in enumerate(campaigns):
        imp = c.get('impressions') or 0
        clk = c.get('clicks') or 0
        ctr = c.get('ctr') or 0
        spend = c.get('cost_usd') or 0
        name = c.get('display_name', c.get('name', 'N/A'))
        bg = ' style="background: #f8f9fa;"' if i % 2 == 0 else ''
        html += f"""
      <tr{bg}>
        <td style="padding: 6px 10px; border-bottom: 1px solid #eee;">{name}</td>
        <td style="padding: 6px 10px; border-bottom: 1px solid #eee; text-align: right;">{imp:,}</td>
        <td style="padding: 6px 10px; border-bottom: 1px solid #eee; text-align: right;">{clk:,}</td>
        <td style="padding: 6px 10px; border-bottom: 1px solid #eee; text-align: right;">{ctr:.2f}%</td>
        <td style="padding: 6px 10px; border-bottom: 1px solid #eee; text-align: right;">${spend:,.2f}</td>
      </tr>"""

    html += """
    </table>

    <p style="font-size: 12px; color: #999; margin-top: 24px; border-top: 1px solid #eee; padding-top: 12px;">
      Generated with LinkedIn Report Automation
    </p>
  </div>
</body>
</html>"""
    return html


def send_report_email(
    recipient_emails,
    subject,
    body_html,
    attachment_paths=None,
    sender_email=None,
    sender_password=None,
    smtp_host=None,
    smtp_port=None,
):
    """Send a report email with optional file attachments.

    Args:
        recipient_emails: List of recipient email addresses.
        subject: Email subject line.
        body_html: HTML string for the email body.
        attachment_paths: Optional list of file paths to attach (PPTX, PDF, etc).
        sender_email: Sender address. Falls back to EMAIL_SENDER env var.
        sender_password: Sender password. Falls back to EMAIL_PASSWORD env var.
        smtp_host: SMTP server hostname. Falls back to EMAIL_SMTP_HOST env var
                   (default: smtp.gmail.com).
        smtp_port: SMTP port number. Falls back to EMAIL_SMTP_PORT env var
                   (default: 587).

    Returns:
        True on success, False on failure.
    """
    sender_email = sender_email or os.environ.get('EMAIL_SENDER', '')
    sender_password = sender_password or os.environ.get('EMAIL_PASSWORD', '')
    smtp_host = smtp_host or os.environ.get('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port = smtp_port or int(os.environ.get('EMAIL_SMTP_PORT', '587'))

    if not sender_email or not sender_password:
        print("  Warning: Email sender credentials not configured. "
              "Set EMAIL_SENDER and EMAIL_PASSWORD.", file=sys.stderr)
        return False

    if not recipient_emails:
        print("  Warning: No recipient emails provided.", file=sys.stderr)
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = subject

        # Attach HTML body
        msg.attach(MIMEText(body_html, 'html'))

        # Attach files
        for filepath in (attachment_paths or []):
            if not os.path.isfile(filepath):
                print(f"  Warning: Attachment not found, skipping: {filepath}",
                      file=sys.stderr)
                continue
            filename = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"',
            )
            msg.attach(part)

        # Connect and send
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())

        print(f"  Email sent to: {', '.join(recipient_emails)}", file=sys.stderr)
        return True

    except smtplib.SMTPAuthenticationError:
        print("  Warning: Email authentication failed. Check EMAIL_SENDER and "
              "EMAIL_PASSWORD. For Gmail, use an App Password.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Warning: Email sending failed: {e}", file=sys.stderr)
        return False
