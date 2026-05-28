#!/usr/bin/env python3
"""
Upload demographics CSV files to a new Google Sheet.
Each campaign gets its own worksheet with all demographic segments.
Returns the Google Sheet URL.
"""

import csv
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(PROJECT_DIR, 'config', 'google_token.json')
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Demographic segment display order
SEGMENT_ORDER = [
    'Job Title Segment',
    'Job Seniority Segment',
    'Job Function Segment',
    'Company Name Segment',
    'Company Industry Segment',
    'Company Size Segment',
    'Location Segment',
    'Contextual Country_Region Segment'
]


def get_credentials():
    """Load saved credentials."""
    if not os.path.exists(TOKEN_FILE):
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds if creds and creds.valid else None


def parse_csv_dir(csv_dir):
    """Parse CSV files and group by campaign name.
    Returns: {campaign_name: {segment_name: [[row1], [row2], ...]}}
    """
    campaigns = {}
    for filename in sorted(os.listdir(csv_dir)):
        if not filename.endswith('.csv'):
            continue
        # Filename format: "Campaign Name - Segment Name.csv"
        parts = filename[:-4].rsplit(' - ', 1)
        if len(parts) != 2:
            continue
        camp_name, seg_name = parts[0].strip(), parts[1].strip()
        filepath = os.path.join(csv_dir, filename)
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
        if camp_name not in campaigns:
            campaigns[camp_name] = {}
        campaigns[camp_name][seg_name] = rows
    return campaigns


def upload_to_sheets(csv_dir, report_date):
    """Create a Google Sheet with demographics data.
    Returns the sheet URL or empty string on failure.
    """
    creds = get_credentials()
    if not creds:
        print("  Google Sheets: No valid credentials found. Skipping upload.", file=sys.stderr)
        return ''

    campaigns = parse_csv_dir(csv_dir)
    if not campaigns:
        print("  Google Sheets: No CSV files found. Skipping.", file=sys.stderr)
        return ''

    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Create spreadsheet with campaign worksheets
        sheet_title = f'LinkedIn Demographics - {report_date}'
        camp_names = list(campaigns.keys())

        spreadsheet_body = {
            'properties': {'title': sheet_title},
            'sheets': [
                {'properties': {'title': name[:100], 'index': i}}
                for i, name in enumerate(camp_names)
            ]
        }

        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        sheet_url = spreadsheet['spreadsheetUrl']

        print(f"  Google Sheets: Created '{sheet_title}'", file=sys.stderr)

        # Populate each worksheet
        for camp_idx, camp_name in enumerate(camp_names):
            segments = campaigns[camp_name]
            all_rows = []

            # Add campaign header
            all_rows.append([f'Campaign: {camp_name}'])
            all_rows.append([])

            # Add each segment in order
            ordered_segs = []
            for seg in SEGMENT_ORDER:
                if seg in segments:
                    ordered_segs.append((seg, segments[seg]))
            # Add any remaining segments not in the order list
            for seg, data in segments.items():
                if seg not in SEGMENT_ORDER:
                    ordered_segs.append((seg, data))

            for seg_name, rows in ordered_segs:
                all_rows.append([seg_name.replace('_', '/')])
                for row in rows:
                    all_rows.append(row)
                all_rows.append([])  # Empty row between segments

            # Write to sheet
            safe_name = camp_name[:100]
            range_name = f"'{safe_name}'!A1"
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': all_rows}
            ).execute()

            # Format: bold segment headers and auto-resize
            sheet_id = spreadsheet['sheets'][camp_idx]['properties']['sheetId']
            requests_body = []

            # Auto-resize columns
            requests_body.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 3
                    }
                }
            })

            # Bold the campaign header row
            requests_body.append({
                'repeatCell': {
                    'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 1},
                    'cell': {'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 14}}},
                    'fields': 'userEnteredFormat.textFormat'
                }
            })

            # Bold segment header rows
            row_idx = 2  # Start after campaign header + empty row
            for seg_name, rows in ordered_segs:
                requests_body.append({
                    'repeatCell': {
                        'range': {'sheetId': sheet_id, 'startRowIndex': row_idx, 'endRowIndex': row_idx + 1, 'startColumnIndex': 0, 'endColumnIndex': 3},
                        'cell': {'userEnteredFormat': {
                            'textFormat': {'bold': True},
                            'backgroundColor': {'red': 0.29, 'green': 0.56, 'blue': 0.85}
                        }},
                        'fields': 'userEnteredFormat.textFormat,userEnteredFormat.backgroundColor'
                    }
                })
                # Bold the CSV header row too
                if rows:
                    requests_body.append({
                        'repeatCell': {
                            'range': {'sheetId': sheet_id, 'startRowIndex': row_idx + 1, 'endRowIndex': row_idx + 2, 'startColumnIndex': 0, 'endColumnIndex': 3},
                            'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                            'fields': 'userEnteredFormat.textFormat'
                        }
                    })
                row_idx += len(rows) + 2  # rows + segment header + empty row

            if requests_body:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests_body}
                ).execute()

            print(f"  Google Sheets: Populated '{camp_name}'", file=sys.stderr)

        # Make the sheet viewable by anyone with the link
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()

        print(f"  Google Sheets: {sheet_url}", file=sys.stderr)
        return sheet_url

    except Exception as e:
        print(f"  Google Sheets: Upload failed - {e}", file=sys.stderr)
        return ''


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python upload_to_sheets.py <csv_dir> <report_date>", file=sys.stderr)
        sys.exit(1)
    url = upload_to_sheets(sys.argv[1], sys.argv[2])
    print(url)
