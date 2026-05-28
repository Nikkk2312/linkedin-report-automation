"""
Export report data to Google Slides.

Creates a professional presentation with title slide, metrics summary,
and per-campaign detail slides using the Google Slides API.

Reuses OAuth credentials from config/google_token.json (same as sheets_uploader).
"""

import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TOKEN_FILE = os.path.join(PROJECT_DIR, 'config', 'google_token.json')
SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive',
]


def _get_credentials(credentials_path=None):
    """Load Google OAuth credentials from token file.

    Args:
        credentials_path: Path to the google_token.json file.
                          Defaults to config/google_token.json.

    Returns:
        Credentials object or None.
    """
    token_file = credentials_path or DEFAULT_TOKEN_FILE
    if not os.path.exists(token_file):
        return None
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
    return creds if creds and creds.valid else None


def _emu(inches):
    """Convert inches to EMU (English Metric Units)."""
    return int(inches * 914400)


def _create_text_box_request(page_id, text, left, top, width, height,
                              font_size=14, bold=False, color=None):
    """Build a Slides API request to create a text box.

    Args:
        page_id: The slide page object ID.
        text: Text content.
        left, top, width, height: Position and size in inches.
        font_size: Font size in points.
        bold: Whether to bold the text.
        color: RGB tuple like (0.04, 0.40, 0.76) or None.

    Returns:
        List of API request dicts.
    """
    import uuid
    element_id = f'textbox_{uuid.uuid4().hex[:12]}'
    requests_list = [
        {
            'createShape': {
                'objectId': element_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': page_id,
                    'size': {
                        'width': {'magnitude': _emu(width), 'unit': 'EMU'},
                        'height': {'magnitude': _emu(height), 'unit': 'EMU'},
                    },
                    'transform': {
                        'scaleX': 1, 'scaleY': 1,
                        'translateX': _emu(left), 'translateY': _emu(top),
                        'unit': 'EMU',
                    },
                },
            },
        },
        {
            'insertText': {
                'objectId': element_id,
                'text': text,
            },
        },
        {
            'updateTextStyle': {
                'objectId': element_id,
                'style': {
                    'fontSize': {'magnitude': font_size, 'unit': 'PT'},
                    'bold': bold,
                    **(
                        {'foregroundColor': {'opaqueColor': {'rgbColor': {
                            'red': color[0], 'green': color[1], 'blue': color[2],
                        }}}}
                        if color else {}
                    ),
                },
                'fields': 'fontSize,bold' + (',foregroundColor' if color else ''),
                'textRange': {'type': 'ALL'},
            },
        },
    ]
    return requests_list


def _create_table_request(page_id, rows_data, left, top, width, height):
    """Build a Slides API request to create a metrics table.

    Args:
        page_id: Slide page object ID.
        rows_data: List of (label, value) tuples.
        left, top, width, height: Position/size in inches.

    Returns:
        List of API request dicts.
    """
    import uuid
    table_id = f'table_{uuid.uuid4().hex[:12]}'
    num_rows = len(rows_data)

    requests_list = [
        {
            'createTable': {
                'objectId': table_id,
                'elementProperties': {
                    'pageObjectId': page_id,
                    'size': {
                        'width': {'magnitude': _emu(width), 'unit': 'EMU'},
                        'height': {'magnitude': _emu(height), 'unit': 'EMU'},
                    },
                    'transform': {
                        'scaleX': 1, 'scaleY': 1,
                        'translateX': _emu(left), 'translateY': _emu(top),
                        'unit': 'EMU',
                    },
                },
                'rows': num_rows,
                'columns': 2,
            },
        },
    ]

    # Insert text into each cell
    for row_idx, (label, value) in enumerate(rows_data):
        for col_idx, text in enumerate([label, value]):
            requests_list.append({
                'insertText': {
                    'objectId': table_id,
                    'cellLocation': {
                        'rowIndex': row_idx,
                        'columnIndex': col_idx,
                    },
                    'text': str(text),
                },
            })

    return requests_list


def export_to_google_slides(report_data, title=None, credentials_path=None):
    """Export report data to a new Google Slides presentation.

    Creates a title slide, a summary slide with key metrics, and
    individual slides for each campaign with performance details.

    Args:
        report_data: Dict with 'campaigns' list and 'report_date' string,
                     as returned by LinkedInClient.fetch_all_campaign_data().
        title: Optional presentation title. Defaults to
               'LinkedIn Campaign Report - <date>'.
        credentials_path: Path to Google OAuth token file. Defaults to
                          config/google_token.json.

    Returns:
        The Google Slides URL string, or empty string on failure.
    """
    creds = _get_credentials(credentials_path)
    if not creds:
        print("  Google Slides: No valid credentials found. Skipping.",
              file=sys.stderr)
        return ''

    campaigns = report_data.get('campaigns', [])
    report_date = report_data.get('report_date', 'N/A')
    pres_title = title or f'LinkedIn Campaign Report - {report_date}'

    try:
        slides_service = build('slides', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Create presentation
        presentation = slides_service.presentations().create(
            body={'title': pres_title}
        ).execute()
        pres_id = presentation['presentationId']
        pres_url = f'https://docs.google.com/presentation/d/{pres_id}/edit'

        # The new presentation has one blank slide by default
        default_slide_id = presentation['slides'][0]['objectId']

        # Aggregate metrics
        total_imp = sum(c.get('impressions') or 0 for c in campaigns)
        total_clk = sum(c.get('clicks') or 0 for c in campaigns)
        total_eng = sum(c.get('engagements') or 0 for c in campaigns)
        total_spend = sum(c.get('cost_usd') or 0.0 for c in campaigns)
        overall_ctr = (total_clk / total_imp * 100) if total_imp else 0

        all_requests = []

        # === Title Slide (use the default first slide) ===
        all_requests.extend(_create_text_box_request(
            default_slide_id, pres_title,
            left=0.5, top=2.0, width=9.0, height=1.5,
            font_size=32, bold=True, color=(0.04, 0.40, 0.76),
        ))
        all_requests.extend(_create_text_box_request(
            default_slide_id,
            f'{len(campaigns)} Campaigns | {report_date}',
            left=0.5, top=3.8, width=9.0, height=0.6,
            font_size=18, color=(0.4, 0.4, 0.4),
        ))

        # === Summary Slide ===
        import uuid
        summary_id = f'summary_{uuid.uuid4().hex[:8]}'
        all_requests.append({
            'createSlide': {
                'objectId': summary_id,
                'insertionIndex': 1,
            },
        })
        all_requests.extend(_create_text_box_request(
            summary_id, 'Executive Summary',
            left=0.5, top=0.3, width=9.0, height=0.6,
            font_size=28, bold=True, color=(0.04, 0.40, 0.76),
        ))

        summary_rows = [
            ('Campaigns', str(len(campaigns))),
            ('Total Impressions', f'{total_imp:,}'),
            ('Total Clicks', f'{total_clk:,}'),
            ('Overall CTR', f'{overall_ctr:.2f}%'),
            ('Total Engagements', f'{total_eng:,}'),
            ('Total Spend', f'${total_spend:,.2f}'),
        ]
        all_requests.extend(_create_table_request(
            summary_id, summary_rows,
            left=0.5, top=1.2, width=9.0, height=3.0,
        ))

        # === Per-Campaign Slides ===
        for idx, camp in enumerate(campaigns):
            camp_slide_id = f'camp_{uuid.uuid4().hex[:8]}'
            all_requests.append({
                'createSlide': {
                    'objectId': camp_slide_id,
                    'insertionIndex': idx + 2,
                },
            })

            camp_name = camp.get('display_name', camp.get('name', f'Campaign {idx + 1}'))
            all_requests.extend(_create_text_box_request(
                camp_slide_id, camp_name,
                left=0.5, top=0.3, width=9.0, height=0.6,
                font_size=24, bold=True, color=(0.04, 0.40, 0.76),
            ))

            imp = camp.get('impressions') or 0
            clk = camp.get('clicks') or 0
            eng = camp.get('engagements') or 0
            ctr = camp.get('ctr') or 0
            cpc = camp.get('cpc') or 0
            spend = camp.get('cost_usd') or 0
            camp_type = camp.get('campaign_type', 'N/A')
            geo = camp.get('geo_display', 'N/A')

            camp_rows = [
                ('Type', camp_type),
                ('Geography', geo),
                ('Impressions', f'{imp:,}'),
                ('Clicks', f'{clk:,}'),
                ('CTR', f'{ctr:.2f}%'),
                ('Engagements', f'{eng:,}'),
                ('CPC', f'${cpc:.2f}'),
                ('Spend', f'${spend:,.2f}'),
            ]
            all_requests.extend(_create_table_request(
                camp_slide_id, camp_rows,
                left=0.5, top=1.2, width=9.0, height=4.0,
            ))

        # Execute all requests in one batch
        if all_requests:
            slides_service.presentations().batchUpdate(
                presentationId=pres_id,
                body={'requests': all_requests},
            ).execute()

        # Make viewable by anyone with the link
        drive_service.permissions().create(
            fileId=pres_id,
            body={'type': 'anyone', 'role': 'reader'},
            fields='id',
        ).execute()

        print(f"  Google Slides: {pres_url}", file=sys.stderr)
        return pres_url

    except Exception as e:
        print(f"  Google Slides: Export failed - {e}", file=sys.stderr)
        return ''
