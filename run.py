#!/usr/bin/env python3
"""
CLI entry point for generating LinkedIn Ad Campaign reports without n8n.

Usage:
    python run.py --token YOUR_TOKEN --account-id 12345 --campaigns 123,456,789
    python run.py --env .env --campaigns all
    python run.py --env .env --campaigns active
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def validate_inputs(args, token, account_id):
    """Validate CLI inputs before proceeding with report generation.

    Args:
        args: Parsed argparse namespace.
        token: Resolved LinkedIn access token.
        account_id: Resolved LinkedIn account ID.

    Raises:
        SystemExit: If any validation fails.
    """
    if not token:
        logger.error("No access token provided. Use --token or set LINKEDIN_ACCESS_TOKEN.")
        sys.exit(1)
    if not account_id:
        logger.error("No account ID provided. Use --account-id or set LINKEDIN_ACCOUNT_ID.")
        sys.exit(1)

    # Validate account_id is numeric
    if not account_id.isdigit():
        logger.error("Account ID must be numeric, got: %s", account_id)
        sys.exit(1)

    # Validate campaign IDs are numeric (if not special keywords)
    campaigns_arg = args.campaigns.strip()
    if campaigns_arg.lower() not in ('all', 'active'):
        for cid in campaigns_arg.split(','):
            cid = cid.strip()
            if cid and not cid.isdigit():
                logger.error("Campaign ID must be numeric, got: %s", cid)
                sys.exit(1)

    # Validate output path is writable
    if args.output:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        if not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except OSError as e:
                logger.error("Output directory is not writable: %s (%s)", out_dir, e)
                sys.exit(1)

    # Validate logo file exists if specified (and not the default)
    if args.logo:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_check = args.logo
        if not os.path.isabs(logo_check):
            logo_check = os.path.join(script_dir, logo_check)
        if not os.path.isfile(logo_check):
            logger.warning("Logo file not found: %s (will proceed without logo)", logo_check)


def main():
    parser = argparse.ArgumentParser(
        description='Generate LinkedIn Ad Campaign Performance Report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --token YOUR_TOKEN --account-id 12345 --campaigns 123,456,789
  python run.py --env .env --campaigns all
  python run.py --env .env --campaigns active
  python run.py --env .env --campaigns 123,456 --output output/my_report.pptx
        """,
    )

    parser.add_argument(
        '--token',
        help='LinkedIn API access token (or set LINKEDIN_ACCESS_TOKEN env var)',
    )
    parser.add_argument(
        '--account-id',
        help='LinkedIn Ad Account ID (or set LINKEDIN_ACCOUNT_ID env var)',
    )
    parser.add_argument(
        '--campaigns',
        required=True,
        help='Campaign IDs: comma-separated (123,456), "all", or "active"',
    )
    parser.add_argument(
        '--env',
        metavar='ENV_FILE',
        help='Path to .env file to load credentials from',
    )
    parser.add_argument(
        '--output', '-o',
        help='Output PPTX path (default: output/LinkedIn_Report_<timestamp>.pptx)',
    )
    parser.add_argument(
        '--logo',
        default='assets/logo.png',
        help='Path to logo image (default: assets/logo.png)',
    )
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only fetch data and save JSON, skip PPTX generation',
    )
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='Also export PDF (requires LibreOffice)',
    )

    args = parser.parse_args()

    # Load .env file if specified
    if args.env:
        env_path = os.path.abspath(args.env)
        if not os.path.isfile(env_path):
            logger.error("Error: .env file not found: %s", env_path)
            sys.exit(1)
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=True)
            logger.info("Loaded environment from: %s", env_path)
        except ImportError:
            logger.error("python-dotenv is required. Install with: pip install python-dotenv")
            sys.exit(1)

    # Resolve credentials
    token = args.token or os.environ.get('LINKEDIN_ACCESS_TOKEN', '')
    account_id = args.account_id or os.environ.get('LINKEDIN_ACCOUNT_ID', '')

    # Validate all inputs
    validate_inputs(args, token, account_id)

    # Determine output paths
    timestamp = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    if args.output:
        output_pptx = args.output
    else:
        output_pptx = os.path.join(output_dir, f'LinkedIn_Report_{timestamp}.pptx')

    json_path = os.path.splitext(output_pptx)[0] + '.json'

    # Import and initialize the LinkedIn client
    from src.linkedin_client import LinkedInClient
    client = LinkedInClient(access_token=token, account_id=account_id)

    # Resolve campaign IDs
    logger.info("Resolving campaigns: %s", args.campaigns)
    campaign_ids = client.get_campaign_ids(args.campaigns)
    if not campaign_ids:
        logger.error("No campaigns found.")
        sys.exit(1)
    logger.info("Found %d campaigns: %s%s",
                len(campaign_ids),
                ', '.join(campaign_ids[:10]),
                '...' if len(campaign_ids) > 10 else '')

    # Fetch all campaign data
    data = client.fetch_all_campaign_data(campaign_ids)

    # Save JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Data saved to: %s", json_path)

    if args.json_only:
        print(json_path)
        return

    # Generate PPTX report
    logger.info("Generating PPTX report...")
    from src.report_generator import generate_report

    # Resolve logo path
    logo_path = args.logo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(logo_path):
        logo_path = os.path.join(script_dir, logo_path)

    generate_report(json_path, output_pptx, logo_path=logo_path)

    # PDF export if requested
    if args.pdf:
        from src.pdf_exporter import export_pdf
        pdf_path = os.path.splitext(output_pptx)[0] + '.pdf'
        result = export_pdf(output_pptx, pdf_path)
        if result:
            print(result)

    print(output_pptx)


if __name__ == '__main__':
    main()
