#!/usr/bin/env python3
"""
Google OAuth Setup — One-time authentication for Google Sheets integration.
Run this script to authenticate with Google and save the token.

Usage:
    python scripts/google_auth.py

You need a Google Cloud OAuth client (Desktop App type).
Place client_secret.json in the config/ directory.
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRET = os.path.join(PROJECT_DIR, 'config', 'client_secret.json')
TOKEN_FILE = os.path.join(PROJECT_DIR, 'config', 'google_token.json')
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def main():
    if not os.path.exists(CLIENT_SECRET):
        print(f"ERROR: {CLIENT_SECRET} not found.")
        print("\nTo set up Google Sheets integration:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (Desktop App type)")
        print("3. Download the JSON and save it as config/client_secret.json")
        sys.exit(1)

    print("Starting Google OAuth flow...")
    print("A browser window will open for authentication.\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0)

    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())

    print(f"\nAuthentication successful!")
    print(f"Token saved to: {TOKEN_FILE}")
    print("Google Sheets integration is now ready.")


if __name__ == '__main__':
    main()
