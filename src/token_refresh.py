"""
LinkedIn OAuth token refresh automation.

Handles checking token expiry, refreshing access tokens using the
LinkedIn OAuth 2.0 refresh token flow, and auto-refreshing when needed.

Environment variables:
    LINKEDIN_CLIENT_ID     - LinkedIn app client ID
    LINKEDIN_CLIENT_SECRET - LinkedIn app client secret
    LINKEDIN_REFRESH_TOKEN - LinkedIn OAuth refresh token
    LINKEDIN_ACCESS_TOKEN  - Current access token (read and updated)
"""

import json
import os
import sys
import time

import requests


LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_INTROSPECT_URL = 'https://www.linkedin.com/oauth/v2/introspectToken'


def check_token_expiry(token):
    """Validate a LinkedIn access token and check its expiry.

    Uses the LinkedIn token introspection endpoint to determine
    whether the token is still valid and how long until it expires.

    Args:
        token: LinkedIn OAuth access token string.

    Returns:
        Dict with keys:
            'valid': bool - Whether the token is currently valid.
            'expires_in': int - Seconds until expiry (0 if expired/unknown).
            'status': str - Human-readable status message.
    """
    if not token:
        return {
            'valid': False,
            'expires_in': 0,
            'status': 'No token provided',
        }

    # Try a lightweight API call to verify the token
    try:
        resp = requests.get(
            'https://api.linkedin.com/v2/me',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10,
        )
        if resp.status_code == 200:
            return {
                'valid': True,
                'expires_in': -1,  # Unknown exact expiry from this check
                'status': 'Token is valid',
            }
        elif resp.status_code == 401:
            return {
                'valid': False,
                'expires_in': 0,
                'status': 'Token is expired or invalid',
            }
        else:
            return {
                'valid': False,
                'expires_in': 0,
                'status': f'Token check returned HTTP {resp.status_code}',
            }
    except Exception as e:
        return {
            'valid': False,
            'expires_in': 0,
            'status': f'Token check failed: {e}',
        }


def refresh_access_token(client_id=None, client_secret=None, refresh_token=None):
    """Refresh a LinkedIn OAuth access token using the refresh token flow.

    Args:
        client_id: LinkedIn app client ID. Falls back to
                   LINKEDIN_CLIENT_ID env var.
        client_secret: LinkedIn app client secret. Falls back to
                       LINKEDIN_CLIENT_SECRET env var.
        refresh_token: LinkedIn OAuth refresh token. Falls back to
                       LINKEDIN_REFRESH_TOKEN env var.

    Returns:
        Dict with keys:
            'access_token': str - The new access token (empty on failure).
            'expires_in': int - Token lifetime in seconds (0 on failure).
            'refresh_token': str - New refresh token if rotated (may be empty).
            'success': bool - Whether the refresh succeeded.
            'error': str - Error message on failure (empty on success).
    """
    client_id = client_id or os.environ.get('LINKEDIN_CLIENT_ID', '')
    client_secret = client_secret or os.environ.get('LINKEDIN_CLIENT_SECRET', '')
    refresh_token = refresh_token or os.environ.get('LINKEDIN_REFRESH_TOKEN', '')

    result = {
        'access_token': '',
        'expires_in': 0,
        'refresh_token': '',
        'success': False,
        'error': '',
    }

    if not client_id or not client_secret:
        result['error'] = ('Missing client credentials. Set LINKEDIN_CLIENT_ID '
                           'and LINKEDIN_CLIENT_SECRET.')
        print(f"  Warning: {result['error']}", file=sys.stderr)
        return result

    if not refresh_token:
        result['error'] = ('Missing refresh token. Set LINKEDIN_REFRESH_TOKEN.')
        print(f"  Warning: {result['error']}", file=sys.stderr)
        return result

    try:
        resp = requests.post(
            LINKEDIN_TOKEN_URL,
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            result['access_token'] = data.get('access_token', '')
            result['expires_in'] = data.get('expires_in', 0)
            result['refresh_token'] = data.get('refresh_token', '')
            result['success'] = True
            print("  Token refreshed successfully.", file=sys.stderr)
        else:
            error_data = {}
            try:
                error_data = resp.json()
            except Exception:
                pass
            result['error'] = (
                error_data.get('error_description')
                or error_data.get('error')
                or f'HTTP {resp.status_code}'
            )
            print(f"  Warning: Token refresh failed: {result['error']}",
                  file=sys.stderr)

    except requests.exceptions.Timeout:
        result['error'] = 'Request timed out'
        print("  Warning: Token refresh request timed out.", file=sys.stderr)
    except Exception as e:
        result['error'] = str(e)
        print(f"  Warning: Token refresh failed: {e}", file=sys.stderr)

    return result


def auto_refresh_if_needed(client_id=None, client_secret=None,
                           refresh_token=None, access_token=None):
    """Check the current access token and refresh it if expired.

    This is a convenience function that combines check_token_expiry()
    and refresh_access_token(). If the current token is still valid,
    it is returned as-is.

    Args:
        client_id: LinkedIn app client ID (or LINKEDIN_CLIENT_ID env).
        client_secret: LinkedIn app client secret (or LINKEDIN_CLIENT_SECRET env).
        refresh_token: LinkedIn refresh token (or LINKEDIN_REFRESH_TOKEN env).
        access_token: Current access token (or LINKEDIN_ACCESS_TOKEN env).

    Returns:
        The valid access token string, or empty string on failure.
    """
    access_token = access_token or os.environ.get('LINKEDIN_ACCESS_TOKEN', '')

    if access_token:
        status = check_token_expiry(access_token)
        if status['valid']:
            print("  Token is still valid, no refresh needed.", file=sys.stderr)
            return access_token

    print("  Token expired or missing, attempting refresh...", file=sys.stderr)
    result = refresh_access_token(client_id, client_secret, refresh_token)

    if result['success'] and result['access_token']:
        # Update the environment variable for downstream use
        os.environ['LINKEDIN_ACCESS_TOKEN'] = result['access_token']
        if result['refresh_token']:
            os.environ['LINKEDIN_REFRESH_TOKEN'] = result['refresh_token']
        return result['access_token']

    print("  Warning: Could not obtain a valid access token.", file=sys.stderr)
    return ''
