#!/usr/bin/env python3
"""
Flask web dashboard for LinkedIn Report Automation.
Single local interface for generating, viewing, and managing reports.

Usage:
    python app.py
    Open http://localhost:5000
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify, send_from_directory,
)

# Project root
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / 'output'
ASSETS_DIR = BASE_DIR / 'assets'
ENV_PATH = BASE_DIR / '.env'

app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))
app.secret_key = os.urandom(24)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# In-memory job tracking
_jobs = {}

# In-memory insights cache
_insights_cache = {}

# In-memory notification center
_notifications = []

# In-memory report comments
_comments = {}

# In-memory report versions
_versions = {}

# In-memory account profiles
_account_profiles = []

# Undo stack
_undo_stack = []

def _add_notification(title, detail='', ntype='info'):
    _notifications.insert(0, {
        'id': f"notif_{int(time.time())}_{len(_notifications)}",
        'title': title,
        'detail': detail,
        'type': ntype,
        'time': datetime.now().strftime('%d %b, %I:%M %p'),
        'read': False,
    })
    if len(_notifications) > 50:
        _notifications.pop()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _load_env():
    values = {}
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                values[key.strip()] = val.strip()
    return values


def _save_env(values):
    sections = [
        ("# LinkedIn API Credentials", [
            'LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_ACCOUNT_ID',
            'LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET', 'LINKEDIN_REFRESH_TOKEN']),
        ("# AI Insights", [
            'AI_INSIGHTS_ENABLED', 'OLLAMA_ENABLED', 'OLLAMA_MODEL', 'OLLAMA_BASE_URL',
            'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']),
        ("# Email Delivery", [
            'EMAIL_SMTP_HOST', 'EMAIL_SMTP_PORT', 'EMAIL_SENDER', 'EMAIL_PASSWORD',
            'REPORT_RECIPIENTS']),
        ("# Slack", ['SLACK_WEBHOOK_URL']),
        ("# Branding", ['BRAND_NAME', 'COMPANY_NAME', 'THEME']),
        ("# Webhook Security", ['WEBHOOK_API_KEY']),
    ]
    lines = []
    for header, keys in sections:
        lines.append(header)
        for k in keys:
            lines.append(f"{k}={values.get(k, '')}")
        lines.append("")
    ENV_PATH.write_text('\n'.join(lines))


def _get_reports_list():
    reports = []
    if not OUTPUT_DIR.is_dir():
        return reports
    groups = {}
    for f in OUTPUT_DIR.iterdir():
        if f.is_file() and f.suffix in ('.pptx', '.json', '.html', '.pdf'):
            stem = f.stem
            if stem not in groups:
                groups[stem] = {'name': stem, 'files': {}, 'mtime': 0}
            groups[stem]['files'][f.suffix] = f.name
            groups[stem]['mtime'] = max(groups[stem]['mtime'], f.stat().st_mtime)

    for stem, grp in groups.items():
        if '.pptx' in grp['files'] or '.json' in grp['files']:
            grp['date'] = datetime.fromtimestamp(grp['mtime']).strftime('%d %b %Y, %I:%M %p')
            grp['timestamp'] = grp['mtime']
            json_file = grp['files'].get('.json')
            if json_file:
                try:
                    data = json.loads((OUTPUT_DIR / json_file).read_text())
                    camps = data.get('campaigns', [])
                    grp['campaign_count'] = len(camps)
                    grp['total_impressions'] = sum(c.get('impressions', 0) or 0 for c in camps)
                    grp['total_clicks'] = sum(c.get('clicks', 0) or 0 for c in camps)
                    grp['total_spend'] = sum(float(c.get('cost_usd', 0) or 0) for c in camps)
                    total_eng = sum(c.get('engagements', 0) or 0 for c in camps)
                    grp['total_engagements'] = total_eng
                    grp['overall_ctr'] = round(
                        (grp['total_clicks'] / grp['total_impressions'] * 100)
                        if grp['total_impressions'] else 0, 2)
                except Exception:
                    grp['campaign_count'] = '?'
            reports.append(grp)

    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    return reports


def _get_report_data(report_name):
    json_path = OUTPUT_DIR / f"{report_name}.json"
    if not json_path.is_file():
        return None
    try:
        return json.loads(json_path.read_text())
    except Exception:
        return None


def _aggregate_campaigns(campaigns):
    total_imp = sum(c.get('impressions', 0) or 0 for c in campaigns)
    total_clicks = sum(c.get('clicks', 0) or 0 for c in campaigns)
    total_spend = sum(float(c.get('cost_usd', 0) or 0) for c in campaigns)
    total_eng = sum(c.get('engagements', 0) or 0 for c in campaigns)
    total_likes = sum(c.get('likes', 0) or 0 for c in campaigns)
    total_comments = sum(c.get('comments', 0) or 0 for c in campaigns)
    total_shares = sum(c.get('shares', 0) or 0 for c in campaigns)
    total_video = sum(c.get('video_views', 0) or 0 for c in campaigns)
    total_leads = sum((c.get('oneClickLeads', 0) or c.get('one_click_leads', 0) or 0) for c in campaigns)
    total_viral = sum(c.get('viral_impressions', 0) or 0 for c in campaigns)
    overall_ctr = (total_clicks / total_imp * 100) if total_imp else 0
    overall_cpc = (total_spend / total_clicks) if total_clicks else 0
    overall_cpm = (total_spend / total_imp * 1000) if total_imp else 0
    eng_rate = (total_eng / total_imp * 100) if total_imp else 0
    return {
        'total_imp': total_imp, 'total_clicks': total_clicks,
        'total_spend': total_spend, 'total_eng': total_eng,
        'total_likes': total_likes, 'total_comments': total_comments,
        'total_shares': total_shares, 'total_video': total_video,
        'total_leads': total_leads, 'total_viral': total_viral,
        'overall_ctr': overall_ctr, 'overall_cpc': overall_cpc,
        'overall_cpm': overall_cpm, 'eng_rate': eng_rate,
    }


def _get_latest_report_data():
    reports = _get_reports_list()
    for r in reports:
        if '.json' in r.get('files', {}):
            data = _get_report_data(r['name'])
            if data and data.get('campaigns'):
                return r, data
    return None, None


def _get_trend_data_from_reports():
    """Build trend data from all report JSON files."""
    reports = _get_reports_list()
    trends = []
    for r in reversed(reports[:20]):  # Last 20, oldest first
        json_file = r['files'].get('.json')
        if not json_file:
            continue
        try:
            data = json.loads((OUTPUT_DIR / json_file).read_text())
            camps = data.get('campaigns', [])
            imp = sum(c.get('impressions', 0) or 0 for c in camps)
            clicks = sum(c.get('clicks', 0) or 0 for c in camps)
            spend = sum(float(c.get('cost_usd', 0) or 0) for c in camps)
            ctr = (clicks / imp * 100) if imp else 0
            trends.append({
                'label': r.get('date', r['name'])[:12],
                'impressions': imp,
                'clicks': clicks,
                'spend': round(spend, 2),
                'ctr': round(ctr, 2),
                'campaigns': len(camps),
            })
        except Exception:
            continue
    return trends


# ─── Routes: Dashboard ──────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    reports = _get_reports_list()
    env = _load_env()
    has_token = bool(env.get('LINKEDIN_ACCESS_TOKEN'))
    has_account = bool(env.get('LINKEDIN_ACCOUNT_ID'))

    # Get latest report KPIs
    latest_meta, latest_data = _get_latest_report_data()
    kpis = None
    prev_kpis = None
    top_campaigns = []
    bottom_campaigns = []
    if latest_data:
        campaigns = latest_data.get('campaigns', [])
        kpis = _aggregate_campaigns(campaigns)
        sorted_by_ctr = sorted(
            [c for c in campaigns if (c.get('impressions', 0) or 0) > 100],
            key=lambda c: c.get('ctr', 0) or 0, reverse=True
        )
        top_campaigns = sorted_by_ctr[:3]
        bottom_campaigns = sorted_by_ctr[-3:][::-1] if len(sorted_by_ctr) > 3 else []

    # Period-over-period: compare with second-latest report
    if len(reports) >= 2:
        second_name = reports[1]['name']
        second_data = _get_report_data(second_name)
        if second_data and second_data.get('campaigns'):
            prev_kpis = _aggregate_campaigns(second_data['campaigns'])

    # Trend sparkline data
    trends = _get_trend_data_from_reports()

    # Detect first-run (no credentials configured)
    needs_onboarding = not has_token and not has_account and len(reports) == 0

    return render_template('dashboard.html',
                           reports=reports, has_token=has_token, has_account=has_account,
                           total_reports=len(reports), jobs=_jobs,
                           kpis=kpis, prev_kpis=prev_kpis, latest_meta=latest_meta,
                           top_campaigns=top_campaigns, bottom_campaigns=bottom_campaigns,
                           trends=trends, needs_onboarding=needs_onboarding)


# ─── Routes: Report Generation ──────────────────────────────────────────────

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    env = _load_env()
    if request.method == 'POST':
        token = request.form.get('token') or env.get('LINKEDIN_ACCESS_TOKEN', '')
        account_id = request.form.get('account_id') or env.get('LINKEDIN_ACCOUNT_ID', '')
        campaigns = request.form.get('campaigns', 'active').strip()
        # Handle selected campaign IDs from the picker
        selected_ids = request.form.get('selected_campaign_ids', '').strip()
        custom_ids = request.form.get('custom_campaign_ids', '').strip()
        if campaigns == 'custom' and (selected_ids or custom_ids):
            campaigns = selected_ids or custom_ids
        generate_html = request.form.get('generate_html') == 'on'
        include_ai = request.form.get('include_ai') == 'on'
        report_title = request.form.get('report_title', '').strip()
        email_recipients = request.form.get('email_recipients', '').strip()
        date_range = request.form.get('date_range', 'last_30').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        granularity = request.form.get('granularity', 'monthly').strip()

        if not token or not account_id:
            flash('Access token and Account ID are required.', 'error')
            return redirect(url_for('generate'))

        job_id = f"job_{int(time.time())}"
        _jobs[job_id] = {
            'status': 'running', 'progress': 0,
            'message': 'Starting report generation...',
            'output_pptx': None, 'output_html': None, 'error': None,
            'started': datetime.now().strftime('%I:%M %p'),
        }

        def _run(jid, tk, acct, camps, do_html, do_ai, title, emails):
            try:
                _jobs[jid]['message'] = 'Connecting to LinkedIn API...'
                _jobs[jid]['progress'] = 10
                from src.linkedin_client import LinkedInClient
                client = LinkedInClient(access_token=tk, account_id=acct)

                _jobs[jid]['message'] = 'Resolving campaigns...'
                _jobs[jid]['progress'] = 20
                campaign_ids = client.get_campaign_ids(camps)
                if not campaign_ids:
                    _jobs[jid]['status'] = 'error'
                    _jobs[jid]['error'] = 'No campaigns found.'
                    return

                _jobs[jid]['message'] = f'Fetching data for {len(campaign_ids)} campaigns...'
                _jobs[jid]['progress'] = 30
                data = client.fetch_all_campaign_data(campaign_ids)

                OUTPUT_DIR.mkdir(exist_ok=True)
                ts = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
                base_name = title or f'LinkedIn_Report_{ts}'
                # Sanitize
                base_name = "".join(c for c in base_name if c.isalnum() or c in ' _-').strip()
                base_name = base_name.replace(' ', '_') or f'LinkedIn_Report_{ts}'
                json_path = OUTPUT_DIR / f'{base_name}.json'
                json_path.write_text(json.dumps(data, indent=2, default=str))

                _jobs[jid]['message'] = 'Generating PPTX report...'
                _jobs[jid]['progress'] = 55
                from src.report_generator import generate_report
                pptx_path = str(OUTPUT_DIR / f'{base_name}.pptx')
                logo_path = str(ASSETS_DIR / 'logo.png')
                generate_report(str(json_path), pptx_path, logo_path=logo_path)
                _jobs[jid]['output_pptx'] = f'{base_name}.pptx'

                if do_html:
                    _jobs[jid]['message'] = 'Generating HTML report...'
                    _jobs[jid]['progress'] = 75
                    from src.html_report import generate_html_report
                    html_path = str(OUTPUT_DIR / f'{base_name}.html')
                    generate_html_report(data, html_path)
                    _jobs[jid]['output_html'] = f'{base_name}.html'

                # Save to data store
                try:
                    from src.data_store import DataStore
                    DataStore().save_report(data)
                except Exception as e:
                    logger.warning("DataStore save failed: %s", e)

                # Email if requested
                if emails:
                    _jobs[jid]['message'] = 'Sending email notifications...'
                    _jobs[jid]['progress'] = 90
                    try:
                        from src.email_sender import send_report_email, format_report_email_body
                        recipients = [r.strip() for r in emails.split(',') if r.strip()]
                        body = format_report_email_body(data)
                        send_report_email(
                            recipient_emails=recipients,
                            subject=f"LinkedIn Campaign Report - {data.get('report_date', '')}",
                            body_html=body,
                            attachment_paths=[pptx_path],
                        )
                    except Exception as e:
                        logger.warning("Email failed: %s", e)

                _jobs[jid]['status'] = 'done'
                _jobs[jid]['progress'] = 100
                _jobs[jid]['message'] = 'Report generated successfully!'
                _jobs[jid]['report_name'] = base_name
                _log_activity('Report generated', base_name)
                # Track version
                if base_name not in _versions:
                    _versions[base_name] = []
                _versions[base_name].append({
                    'version': len(_versions[base_name]) + 1,
                    'time': datetime.now().strftime('%d %b %Y, %I:%M %p'),
                    'campaigns': len(campaign_ids),
                    'type': 'full_generate',
                })

            except Exception as e:
                _jobs[jid]['status'] = 'error'
                _jobs[jid]['error'] = str(e)
                _jobs[jid]['message'] = f'Error: {e}'
                logger.exception("Report generation failed")

        thread = threading.Thread(
            target=_run,
            args=(job_id, token, account_id, campaigns, generate_html, include_ai, report_title, email_recipients),
            daemon=True)
        thread.start()
        return redirect(url_for('job_status_page', job_id=job_id))

    return render_template('generate.html', env=env)


@app.route('/regenerate/<report_name>')
def regenerate_from_data(report_name):
    """Re-generate PPTX from existing JSON data (skip API fetch)."""
    data = _get_report_data(report_name)
    if not data:
        flash('JSON data not found for this report.', 'error')
        return redirect(url_for('dashboard'))

    try:
        json_path = str(OUTPUT_DIR / f"{report_name}.json")
        pptx_path = str(OUTPUT_DIR / f"{report_name}_v2.pptx")
        logo_path = str(ASSETS_DIR / 'logo.png')
        from src.report_generator import generate_report
        generate_report(json_path, pptx_path, logo_path=logo_path)
        flash(f'Report regenerated: {report_name}_v2.pptx', 'success')
    except Exception as e:
        flash(f'Regeneration failed: {e}', 'error')

    return redirect(url_for('dashboard'))


# ─── Routes: Job Status ─────────────────────────────────────────────────────

@app.route('/job/<job_id>')
def job_status_page(job_id):
    job = _jobs.get(job_id)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('job_status.html', job=job, job_id=job_id)


@app.route('/api/job/<job_id>')
def job_status_api(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({'error': 'not found'}), 404
    return jsonify(job)


# ─── Routes: Report Viewer ──────────────────────────────────────────────────

@app.route('/report/<report_name>')
def view_report(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))

    campaigns = data.get('campaigns', [])
    report_date = data.get('report_date', 'N/A')
    agg = _aggregate_campaigns(campaigns)

    # Campaign types for filter
    campaign_types = sorted(set(c.get('campaign_type', 'Other') for c in campaigns))

    # Monthly trends
    monthly = {}
    for c in campaigns:
        for m in c.get('monthly_trends', []):
            label = m.get('month', 'Unknown')
            if label not in monthly:
                monthly[label] = {'impressions': 0, 'clicks': 0, 'spend': 0}
            monthly[label]['impressions'] += m.get('impressions', 0)
            monthly[label]['clicks'] += m.get('clicks', 0)
            monthly[label]['spend'] += m.get('cost', 0)

    # Engagement breakdown
    engagement_data = []
    for c in campaigns:
        engagement_data.append({
            'name': (c.get('display_name') or c.get('name', 'Unknown'))[:25],
            'likes': c.get('likes', 0) or 0,
            'comments': c.get('comments', 0) or 0,
            'shares': c.get('shares', 0) or 0,
        })

    # Check which files exist
    files = {}
    for ext in ['.pptx', '.json', '.html', '.pdf']:
        if (OUTPUT_DIR / f"{report_name}{ext}").is_file():
            files[ext] = True

    return render_template('report_view.html',
                           report_name=report_name, report_date=report_date,
                           campaigns=campaigns, agg=agg,
                           campaign_types=campaign_types,
                           monthly=monthly, engagement_data=engagement_data,
                           files=files)


# ─── Routes: Demographics ───────────────────────────────────────────────────

@app.route('/demographics/<report_name>')
def demographics(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))

    campaigns = data.get('campaigns', [])
    campaign_names = [c.get('display_name', c.get('name', 'Unknown')) for c in campaigns]

    # Aggregate demographics across all campaigns
    pivot_types = [
        ('MEMBER_INDUSTRY', 'Industry'),
        ('MEMBER_SENIORITY', 'Seniority'),
        ('MEMBER_JOB_FUNCTION', 'Job Function'),
        ('MEMBER_JOB_TITLE', 'Job Title'),
        ('MEMBER_COMPANY_SIZE', 'Company Size'),
        ('MEMBER_COMPANY', 'Company'),
        ('MEMBER_REGION_V2', 'Region'),
        ('MEMBER_COUNTRY_V2', 'Country'),
    ]

    aggregated = {}
    for pivot_key, label in pivot_types:
        merged = {}
        for c in campaigns:
            demos = c.get('demographics', {})
            for entry in demos.get(pivot_key, []):
                name = entry.get('displayName', 'Unknown')
                if name not in merged:
                    merged[name] = {'impressions': 0, 'clicks': 0}
                merged[name]['impressions'] += entry.get('impressions', 0) or 0
                merged[name]['clicks'] += entry.get('clicks', 0) or 0

        if merged:
            items = []
            for name, vals in merged.items():
                ctr = (vals['clicks'] / vals['impressions'] * 100) if vals['impressions'] else 0
                items.append({
                    'name': name, 'impressions': vals['impressions'],
                    'clicks': vals['clicks'], 'ctr': round(ctr, 2),
                })
            items.sort(key=lambda x: x['impressions'], reverse=True)
            aggregated[label] = items[:20]  # Top 20

    # Per-campaign selector
    selected_campaign = request.args.get('campaign', '')

    return render_template('demographics.html',
                           report_name=report_name,
                           campaigns=campaigns,
                           campaign_names=campaign_names,
                           aggregated=aggregated,
                           pivot_types=pivot_types,
                           selected_campaign=selected_campaign)


# ─── Routes: AI Insights ────────────────────────────────────────────────────

@app.route('/insights/<report_name>')
def insights(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))

    campaigns = data.get('campaigns', [])
    return render_template('insights.html',
                           report_name=report_name,
                           campaigns=campaigns,
                           agg=_aggregate_campaigns(campaigns))


@app.route('/api/insights/<report_name>')
def api_generate_insights(report_name):
    # Return cached results if available
    force = request.args.get('force', '') == '1'
    if not force and report_name in _insights_cache:
        return jsonify(_insights_cache[report_name])

    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404

    campaigns = data.get('campaigns', [])
    result = {}

    # AI Insights
    try:
        from src.ollama_insights import generate_insights, generate_executive_summary
        result['insights'] = generate_insights(campaigns)
        result['executive_summary'] = generate_executive_summary(campaigns)
    except Exception as e:
        result['insights'] = []
        result['executive_summary'] = f'AI insights unavailable: {e}'

    # Budget optimization
    try:
        from src.budget_optimizer import optimize_budget
        result['budget'] = optimize_budget(campaigns)
    except Exception as e:
        result['budget'] = []

    # Audience recommendations
    try:
        from src.audience_recommender import generate_all_recommendations
        result['audience'] = generate_all_recommendations(data)
    except Exception as e:
        result['audience'] = {}

    # A/B test analysis
    try:
        from src.ab_test_analyzer import analyze_campaign_creatives
        ab_results = {}
        for c in campaigns:
            ab = analyze_campaign_creatives(c)
            if ab and not ab.get('error'):
                ab_results[c.get('id', '')] = ab
        result['ab_tests'] = ab_results
    except Exception as e:
        result['ab_tests'] = {}

    # Cache the results
    result['cached_at'] = datetime.now().strftime('%d %b %Y, %I:%M %p')
    _insights_cache[report_name] = result
    _add_notification('AI Insights generated', f'Insights cached for {report_name}', 'success')

    return jsonify(result)


# ─── Routes: Budget Analysis ────────────────────────────────────────────────

@app.route('/budget/<report_name>')
def budget_analysis(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))

    campaigns = data.get('campaigns', [])
    agg = _aggregate_campaigns(campaigns)

    # Run budget optimizer
    budget_suggestions = []
    try:
        from src.budget_optimizer import optimize_budget
        budget_suggestions = optimize_budget(campaigns)
    except Exception as e:
        logger.warning("Budget optimizer failed: %s", e)

    return render_template('budget.html',
                           report_name=report_name,
                           campaigns=campaigns,
                           agg=agg,
                           budget_suggestions=budget_suggestions)


# ─── Routes: Historical Trends ──────────────────────────────────────────────

@app.route('/trends')
def trends_page():
    trends = _get_trend_data_from_reports()

    # Also try DataStore
    ds_trends = {}
    try:
        from src.data_store import DataStore
        ds = DataStore()
        for metric in ['total_impressions', 'total_clicks', 'total_spend', 'overall_ctr']:
            ds_trends[metric] = ds.get_trend(metric, limit=30)
    except Exception:
        pass

    return render_template('trends.html', trends=trends, ds_trends=ds_trends)


# ─── Routes: File Downloads ─────────────────────────────────────────────────

@app.route('/download/<filename>')
def download_file(filename):
    safe_path = OUTPUT_DIR / filename
    if not safe_path.is_file() or OUTPUT_DIR.resolve() not in safe_path.resolve().parents and safe_path.resolve().parent != OUTPUT_DIR.resolve():
        flash('File not found.', 'error')
        return redirect(url_for('dashboard'))
    return send_file(safe_path, as_attachment=True)


@app.route('/view-html/<filename>')
def view_html_report(filename):
    safe_path = OUTPUT_DIR / filename
    if not safe_path.is_file() or not filename.endswith('.html'):
        flash('File not found.', 'error')
        return redirect(url_for('dashboard'))
    return send_from_directory(str(OUTPUT_DIR), filename)


@app.route('/api/export-csv/<report_name>')
def export_csv(report_name):
    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404

    campaigns = data.get('campaigns', [])
    lines = ['Campaign,Type,Status,Impressions,Clicks,CTR,CPC,Spend,Engagements,Likes,Comments,Shares']
    for c in campaigns:
        name = (c.get('display_name') or c.get('name', 'Unknown')).replace(',', ' ')
        lines.append(
            f"{name},{c.get('campaign_type','')},{c.get('status','')},"
            f"{c.get('impressions',0) or 0},{c.get('clicks',0) or 0},"
            f"{c.get('ctr',0) or 0:.2f},{c.get('cpc',0) or 0:.2f},"
            f"{c.get('cost_usd',0) or 0:.2f},{c.get('engagements',0) or 0},"
            f"{c.get('likes',0) or 0},{c.get('comments',0) or 0},{c.get('shares',0) or 0}"
        )

    csv_content = '\n'.join(lines)
    csv_path = OUTPUT_DIR / f"{report_name}.csv"
    csv_path.write_text(csv_content)
    return send_file(csv_path, as_attachment=True, download_name=f"{report_name}.csv")


# ─── Routes: Settings ───────────────────────────────────────────────────────

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        env = _load_env()
        for key in request.form:
            env[key] = request.form[key]
        ai = request.form.get('AI_PROVIDER', 'ollama')
        if ai == 'none':
            env['AI_INSIGHTS_ENABLED'] = 'false'
            env['OLLAMA_ENABLED'] = 'false'
        elif ai == 'ollama':
            env['AI_INSIGHTS_ENABLED'] = 'true'
            env['OLLAMA_ENABLED'] = 'true'
        else:
            env['AI_INSIGHTS_ENABLED'] = 'true'
            env['OLLAMA_ENABLED'] = 'false'

        _save_env(env)
        for k, v in env.items():
            os.environ[k] = v
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))

    env = _load_env()

    # Check Ollama status
    ollama_ok = False
    try:
        import requests as req
        resp = req.get('http://localhost:11434/api/tags', timeout=3)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    return render_template('settings.html', env=env, ollama_ok=ollama_ok)


# ─── API Routes ──────────────────────────────────────────────────────────────

@app.route('/api/test-linkedin')
def test_linkedin():
    token = request.args.get('token', '')
    account = request.args.get('account', '')
    if not token or not account:
        return jsonify({'ok': False, 'message': 'Token and Account ID required'})
    try:
        import requests as req
        resp = req.get(
            f'https://api.linkedin.com/rest/adAccounts/{account}/adCampaigns?q=search&count=1',
            headers={'Authorization': f'Bearer {token}',
                     'LinkedIn-Version': '202503',
                     'X-Restli-Protocol-Version': '2.0.0'},
            timeout=10)
        if resp.status_code == 200:
            return jsonify({'ok': True, 'message': f'Connected to account {account}!'})
        elif resp.status_code == 401:
            return jsonify({'ok': False, 'message': 'Invalid or expired access token'})
        return jsonify({'ok': False, 'message': f'API error: {resp.status_code}'})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


@app.route('/api/list-campaigns')
def api_list_campaigns():
    """Fetch campaigns from LinkedIn for the campaign picker."""
    token = request.args.get('token', '')
    account = request.args.get('account', '')
    status = request.args.get('status', '')  # 'active', 'all'
    if not token or not account:
        return jsonify({'ok': False, 'campaigns': [], 'message': 'Token and Account ID required'})
    try:
        import requests as req
        url = f'https://api.linkedin.com/rest/adAccounts/{account}/adCampaigns?q=search&count=100'
        resp = req.get(url, headers={
            'Authorization': f'Bearer {token}',
            'LinkedIn-Version': '202503',
            'X-Restli-Protocol-Version': '2.0.0',
        }, timeout=15)
        if resp.status_code != 200:
            return jsonify({'ok': False, 'campaigns': [],
                            'message': f'API error {resp.status_code}: {resp.text[:200]}'})
        elements = resp.json().get('elements', [])
        campaigns = []
        for c in elements:
            s = c.get('status', 'UNKNOWN')
            if s == 'REMOVED':
                continue
            if status == 'active' and s != 'ACTIVE':
                continue
            campaigns.append({
                'id': str(c.get('id', '')),
                'name': c.get('name', f"Campaign {c.get('id', '?')}"),
                'status': s,
                'type': c.get('type', ''),
                'objective': c.get('objectiveType', c.get('objective', '')),
                'costType': c.get('costType', ''),
            })
        campaigns.sort(key=lambda x: (0 if x['status'] == 'ACTIVE' else 1, x['name']))
        return jsonify({'ok': True, 'campaigns': campaigns, 'count': len(campaigns)})
    except Exception as e:
        return jsonify({'ok': False, 'campaigns': [], 'message': str(e)})


@app.route('/api/test-ollama')
def test_ollama():
    try:
        import requests as req
        resp = req.get('http://localhost:11434/api/tags', timeout=5)
        if resp.status_code == 200:
            models = [m.get('name', '') for m in resp.json().get('models', [])]
            return jsonify({'ok': True, 'message': f'Connected! Models: {", ".join(models[:5])}'})
    except Exception:
        pass
    return jsonify({'ok': False, 'message': 'Ollama not running.'})


@app.route('/api/reports')
def api_reports():
    return jsonify(_get_reports_list())


@app.route('/api/campaign/<report_name>/<campaign_id>')
def api_campaign_detail(report_name, campaign_id):
    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404
    for c in data.get('campaigns', []):
        if str(c.get('id', '')) == campaign_id:
            return jsonify(c)
    return jsonify({'error': 'campaign not found'}), 404


# ─── Routes: Funnel Visualization ──────────────────────────────────

@app.route('/funnel/<report_name>')
def funnel_page(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))
    campaigns = data.get('campaigns', [])
    agg = _aggregate_campaigns(campaigns)
    return render_template('funnel.html', report_name=report_name, campaigns=campaigns, agg=agg)


# ─── Routes: Compare Reports ──────────────────────────────────────

@app.route('/compare')
def compare_page():
    reports = _get_reports_list()
    selected = request.args.getlist('reports')
    comparison = []
    if selected:
        for name in selected[:5]:
            data = _get_report_data(name)
            if data and data.get('campaigns'):
                agg = _aggregate_campaigns(data['campaigns'])
                comparison.append({
                    'name': name,
                    'campaigns': len(data['campaigns']),
                    **agg,
                })
    return render_template('compare.html', reports=reports, selected=selected, comparison=comparison)


# ─── Routes: Schedule Manager ─────────────────────────────────────

_schedules = []

@app.route('/schedules', methods=['GET', 'POST'])
def schedule_page():
    if request.method == 'POST':
        schedule = {
            'id': f"sched_{int(time.time())}",
            'name': request.form.get('name', 'Unnamed Schedule'),
            'frequency': request.form.get('frequency', 'weekly'),
            'day': request.form.get('day', 'monday'),
            'time': request.form.get('time', '09:00'),
            'campaigns': request.form.get('campaigns', 'active'),
            'email_recipients': request.form.get('email_recipients', ''),
            'generate_html': request.form.get('generate_html') == 'on',
            'include_ai': request.form.get('include_ai') == 'on',
            'enabled': True,
            'last_run': None,
            'created': datetime.now().strftime('%d %b %Y'),
        }
        _schedules.append(schedule)
        flash('Schedule created!', 'success')
        return redirect(url_for('schedule_page'))

    return render_template('schedules.html', schedules=_schedules)


@app.route('/api/schedule/<schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    for s in _schedules:
        if s['id'] == schedule_id:
            s['enabled'] = not s['enabled']
            return jsonify({'ok': True, 'enabled': s['enabled']})
    return jsonify({'error': 'not found'}), 404


@app.route('/api/schedule/<schedule_id>/delete', methods=['POST'])
def delete_schedule(schedule_id):
    global _schedules
    _schedules = [s for s in _schedules if s['id'] != schedule_id]
    return jsonify({'ok': True})


# ─── Routes: Alerts Configuration ─────────────────────────────────

_alerts = []

@app.route('/alerts', methods=['GET', 'POST'])
def alerts_page():
    if request.method == 'POST':
        alert = {
            'id': f"alert_{int(time.time())}",
            'name': request.form.get('name', 'Unnamed Alert'),
            'metric': request.form.get('metric', 'ctr'),
            'condition': request.form.get('condition', 'below'),
            'threshold': float(request.form.get('threshold', 0) or 0),
            'notify_email': request.form.get('notify_email', ''),
            'notify_slack': request.form.get('notify_slack') == 'on',
            'enabled': True,
            'created': datetime.now().strftime('%d %b %Y'),
            'last_triggered': None,
        }
        _alerts.append(alert)
        flash('Alert created!', 'success')
        return redirect(url_for('alerts_page'))

    return render_template('alerts.html', alerts=_alerts)


@app.route('/api/alert/<alert_id>/toggle', methods=['POST'])
def toggle_alert(alert_id):
    for a in _alerts:
        if a['id'] == alert_id:
            a['enabled'] = not a['enabled']
            return jsonify({'ok': True, 'enabled': a['enabled']})
    return jsonify({'error': 'not found'}), 404


@app.route('/api/alert/<alert_id>/delete', methods=['POST'])
def delete_alert(alert_id):
    global _alerts
    _alerts = [a for a in _alerts if a['id'] != alert_id]
    return jsonify({'ok': True})


# ─── Routes: Report Management ────────────────────────────────────

@app.route('/api/delete-report/<report_name>', methods=['POST'])
def delete_report(report_name):
    deleted = []
    for ext in ['.pptx', '.json', '.html', '.pdf', '.csv']:
        path = OUTPUT_DIR / f"{report_name}{ext}"
        if path.is_file():
            path.unlink()
            deleted.append(ext)
    if deleted:
        return jsonify({'ok': True, 'deleted': deleted})
    return jsonify({'ok': False, 'message': 'No files found'}), 404


@app.route('/api/export-pdf/<report_name>')
def export_pdf(report_name):
    """Generate and download PDF from report data."""
    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404
    try:
        from src.pdf_exporter import export_pdf as gen_pdf
        pdf_path = str(OUTPUT_DIR / f"{report_name}.pdf")
        pptx_path = str(OUTPUT_DIR / f"{report_name}.pptx")
        gen_pdf(pptx_path, pdf_path)
        return send_file(pdf_path, as_attachment=True, download_name=f"{report_name}.pdf")
    except ImportError:
        return jsonify({'error': 'PDF exporter not available. Install weasyprint or reportlab.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email-report/<report_name>', methods=['POST'])
def email_report(report_name):
    """Send report via email from the report viewer."""
    recipients = request.json.get('recipients', '')
    if not recipients:
        return jsonify({'ok': False, 'message': 'No recipients provided'})

    data = _get_report_data(report_name)
    if not data:
        return jsonify({'ok': False, 'message': 'Report not found'})

    try:
        from src.email_sender import send_report_email, format_report_email_body
        recipient_list = [r.strip() for r in recipients.split(',') if r.strip()]
        body = format_report_email_body(data)
        attachments = []
        pptx = OUTPUT_DIR / f"{report_name}.pptx"
        if pptx.is_file():
            attachments.append(str(pptx))

        send_report_email(
            recipient_emails=recipient_list,
            subject=f"LinkedIn Campaign Report - {report_name}",
            body_html=body,
            attachment_paths=attachments,
        )
        return jsonify({'ok': True, 'message': f'Report sent to {len(recipient_list)} recipient(s)!'})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


@app.route('/api/refresh-token', methods=['POST'])
def refresh_token():
    """Attempt to refresh the LinkedIn access token."""
    env = _load_env()
    client_id = env.get('LINKEDIN_CLIENT_ID')
    client_secret = env.get('LINKEDIN_CLIENT_SECRET')
    refresh_tok = env.get('LINKEDIN_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_tok]):
        return jsonify({'ok': False, 'message': 'Client ID, Client Secret, and Refresh Token are required'})

    try:
        from src.token_refresh import refresh_access_token
        new_token = refresh_access_token(client_id, client_secret, refresh_tok)
        if new_token:
            env['LINKEDIN_ACCESS_TOKEN'] = new_token
            _save_env(env)
            os.environ['LINKEDIN_ACCESS_TOKEN'] = new_token
            return jsonify({'ok': True, 'message': 'Token refreshed successfully!'})
        return jsonify({'ok': False, 'message': 'Token refresh returned empty result'})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


@app.route('/api/health-scores/<report_name>')
def api_health_scores(report_name):
    """Calculate health scores for all campaigns in a report."""
    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404

    campaigns = data.get('campaigns', [])
    scores = []
    for c in campaigns:
        ctr = c.get('ctr', 0) or 0
        cpc = c.get('cpc', 0) or 0
        imp = c.get('impressions', 0) or 0
        eng = c.get('engagements', 0) or 0
        eng_rate = (eng / imp * 100) if imp else 0

        ctr_score = min(ctr / 0.56 * 50, 100)
        cpc_score = min(5.58 / cpc * 50, 100) if cpc > 0 else 50
        eng_score = min(eng_rate / 0.5 * 50, 100)
        total = round(ctr_score * 0.4 + cpc_score * 0.35 + eng_score * 0.25)

        label = 'Excellent' if total >= 75 else 'Good' if total >= 50 else 'Fair' if total >= 25 else 'Poor'
        scores.append({
            'id': c.get('id'),
            'name': c.get('display_name', c.get('name', 'Unknown')),
            'score': total,
            'label': label,
            'breakdown': {
                'ctr': round(ctr_score),
                'cpc': round(cpc_score),
                'engagement': round(eng_score),
            }
        })

    return jsonify(scores)


@app.route('/api/compare-data')
def api_compare_data():
    """Return comparison data for selected reports."""
    names = request.args.getlist('reports')
    result = []
    for name in names[:5]:
        data = _get_report_data(name)
        if data and data.get('campaigns'):
            agg = _aggregate_campaigns(data['campaigns'])
            result.append({'name': name, 'campaigns': len(data['campaigns']), **agg})
    return jsonify(result)


# ─── Routes: Campaign Detail ──────────────────────────────────────

@app.route('/campaign/<report_name>/<campaign_id>')
def campaign_detail(report_name, campaign_id):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))
    campaign = None
    for c in data.get('campaigns', []):
        if str(c.get('id', '')) == campaign_id:
            campaign = c
            break
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('view_report', report_name=report_name))
    return render_template('campaign_detail.html',
                           report_name=report_name, campaign=campaign)


# ─── Routes: Budget What-If Simulator ─────────────────────────────

@app.route('/whatif/<report_name>')
def whatif_page(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))
    campaigns = data.get('campaigns', [])
    agg = _aggregate_campaigns(campaigns)
    return render_template('whatif.html', report_name=report_name,
                           campaigns=campaigns, agg=agg)


# ─── Routes: Glossary / Help ──────────────────────────────────────

@app.route('/glossary')
def glossary_page():
    return render_template('glossary.html')


# ─── Routes: Activity Log ─────────────────────────────────────────

_activity_log = []

def _log_activity(action, detail='', notify=True):
    _activity_log.insert(0, {
        'time': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'action': action,
        'detail': detail,
    })
    if len(_activity_log) > 200:
        _activity_log.pop()
    if notify:
        _add_notification(action, detail)

@app.route('/activity')
def activity_page():
    return render_template('activity.html', log=_activity_log)


# ─── Routes: Report Templates ─────────────────────────────────────

_templates = [
    {'id': 'weekly_active', 'name': 'Weekly Active Campaigns',
     'campaigns': 'active', 'html': True, 'ai': True,
     'description': 'Standard weekly report for all active campaigns'},
    {'id': 'monthly_all', 'name': 'Monthly Full Report',
     'campaigns': 'all', 'html': True, 'ai': True,
     'description': 'Comprehensive monthly report for all campaigns'},
    {'id': 'quick_active', 'name': 'Quick Active Summary',
     'campaigns': 'active', 'html': False, 'ai': False,
     'description': 'Fast PPTX-only report without HTML or AI'},
]

@app.route('/templates')
def templates_page():
    env = _load_env()
    return render_template('report_templates.html', templates=_templates, env=env)


# ─── API: Favorites / Starring ─────────────────────────────────────

_favorites = set()

@app.route('/api/favorite/<report_name>', methods=['POST'])
def toggle_favorite(report_name):
    if report_name in _favorites:
        _favorites.discard(report_name)
        return jsonify({'ok': True, 'favorited': False})
    _favorites.add(report_name)
    return jsonify({'ok': True, 'favorited': True})


@app.route('/api/favorites')
def get_favorites():
    return jsonify(list(_favorites))


# ─── API: Report Notes / Annotations ───────────────────────────────

_notes = {}

@app.route('/api/notes/<report_name>', methods=['GET', 'POST'])
def report_notes(report_name):
    if request.method == 'POST':
        note = request.json.get('note', '').strip()
        if not note:
            return jsonify({'ok': False, 'message': 'Note text required'}), 400
        if report_name not in _notes:
            _notes[report_name] = []
        _notes[report_name].insert(0, {
            'text': note,
            'time': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        })
        _log_activity('Note added', f'{report_name}: {note[:50]}')
        return jsonify({'ok': True})
    return jsonify(_notes.get(report_name, []))


# ─── API: Data Quality Check ──────────────────────────────────────

@app.route('/api/data-quality/<report_name>')
def data_quality(report_name):
    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404

    campaigns = data.get('campaigns', [])
    issues = []
    score = 100

    # Check for campaigns with zero impressions
    zero_imp = [c for c in campaigns if not c.get('impressions')]
    if zero_imp:
        issues.append({'severity': 'warning', 'message': f'{len(zero_imp)} campaign(s) with zero impressions'})
        score -= len(zero_imp) * 5

    # Check for missing names
    no_name = [c for c in campaigns if not c.get('display_name') and not c.get('name')]
    if no_name:
        issues.append({'severity': 'warning', 'message': f'{len(no_name)} campaign(s) missing display names'})
        score -= len(no_name) * 3

    # Check for missing demographics
    no_demo = [c for c in campaigns if not c.get('demographics')]
    if no_demo:
        issues.append({'severity': 'info', 'message': f'{len(no_demo)} campaign(s) without demographic data'})
        score -= len(no_demo) * 2

    # Check for unusually high CPC
    high_cpc = [c for c in campaigns if (c.get('cpc', 0) or 0) > 20]
    if high_cpc:
        issues.append({'severity': 'danger', 'message': f'{len(high_cpc)} campaign(s) with CPC > $20'})
        score -= len(high_cpc) * 5

    # Check for unusually low CTR
    low_ctr = [c for c in campaigns if (c.get('impressions', 0) or 0) > 1000 and (c.get('ctr', 0) or 0) < 0.1]
    if low_ctr:
        issues.append({'severity': 'warning', 'message': f'{len(low_ctr)} campaign(s) with CTR below 0.1%'})
        score -= len(low_ctr) * 5

    # Check for missing creatives
    no_creatives = [c for c in campaigns if not c.get('creatives')]
    if no_creatives and len(no_creatives) < len(campaigns):
        issues.append({'severity': 'info', 'message': f'{len(no_creatives)} campaign(s) without creative data'})
        score -= 2

    # Missing report date
    if not data.get('report_date'):
        issues.append({'severity': 'info', 'message': 'Report date not set'})
        score -= 3

    if not issues:
        issues.append({'severity': 'success', 'message': 'All data quality checks passed'})

    score = max(0, min(100, score))
    return jsonify({'score': score, 'issues': issues, 'total_campaigns': len(campaigns)})


# ─── API: Dashboard Summary Stats ─────────────────────────────────

@app.route('/api/dashboard-summary')
def dashboard_summary():
    """Quick summary for auto-refresh."""
    reports = _get_reports_list()
    _, latest_data = _get_latest_report_data()
    kpis = _aggregate_campaigns(latest_data.get('campaigns', [])) if latest_data else None
    running_jobs = sum(1 for j in _jobs.values() if j.get('status') == 'running')
    return jsonify({
        'total_reports': len(reports),
        'running_jobs': running_jobs,
        'kpis': kpis,
        'favorites': list(_favorites),
    })


# ─── API: Export Table as CSV ──────────────────────────────────────

@app.route('/api/export-demographics-csv/<report_name>/<pivot>')
def export_demographics_csv(report_name, pivot):
    data = _get_report_data(report_name)
    if not data:
        return jsonify({'error': 'not found'}), 404

    campaigns = data.get('campaigns', [])
    merged = {}
    for c in campaigns:
        demos = c.get('demographics', {})
        for entry in demos.get(pivot, []):
            name = entry.get('displayName', 'Unknown')
            if name not in merged:
                merged[name] = {'impressions': 0, 'clicks': 0}
            merged[name]['impressions'] += entry.get('impressions', 0) or 0
            merged[name]['clicks'] += entry.get('clicks', 0) or 0

    lines = ['Name,Impressions,Clicks,CTR']
    for name, vals in sorted(merged.items(), key=lambda x: x[1]['impressions'], reverse=True):
        ctr = (vals['clicks'] / vals['impressions'] * 100) if vals['impressions'] else 0
        lines.append(f'"{name}",{vals["impressions"]},{vals["clicks"]},{ctr:.2f}')

    import io
    from flask import Response
    return Response(
        '\n'.join(lines),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={report_name}_{pivot}.csv'}
    )


# ─── API: Export / Import Settings ────────────────────────────────

@app.route('/api/export-settings')
def export_settings():
    env = _load_env()
    # Redact sensitive values
    safe = {}
    sensitive = {'LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_CLIENT_SECRET', 'LINKEDIN_REFRESH_TOKEN',
                 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'EMAIL_PASSWORD', 'WEBHOOK_API_KEY'}
    for k, v in env.items():
        safe[k] = '***REDACTED***' if k in sensitive and v else v
    import io
    from flask import Response
    return Response(
        json.dumps(safe, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=settings_export.json'}
    )


@app.route('/api/import-settings', methods=['POST'])
def import_settings():
    try:
        data = request.json
        env = _load_env()
        imported = 0
        for k, v in data.items():
            if v and v != '***REDACTED***':
                env[k] = v
                imported += 1
        _save_env(env)
        for k, v in env.items():
            os.environ[k] = v
        return jsonify({'ok': True, 'message': f'Imported {imported} settings'})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


# ─── API: Bulk Report Operations ──────────────────────────────────

@app.route('/api/bulk-delete', methods=['POST'])
def bulk_delete_reports():
    names = request.json.get('names', [])
    deleted = 0
    for name in names:
        for ext in ['.pptx', '.json', '.html', '.pdf', '.csv']:
            path = OUTPUT_DIR / f"{name}{ext}"
            if path.is_file():
                path.unlink()
                deleted += 1
    _log_activity('Bulk delete', f'{len(names)} reports deleted')
    return jsonify({'ok': True, 'deleted_files': deleted, 'reports': len(names)})


@app.route('/api/bulk-export', methods=['POST'])
def bulk_export_csv():
    """Export multiple reports to a single CSV."""
    names = request.json.get('names', [])
    lines = ['Report,Campaign,Type,Status,Impressions,Clicks,CTR,CPC,Spend,Engagements']
    for name in names:
        data = _get_report_data(name)
        if not data:
            continue
        for c in data.get('campaigns', []):
            cname = (c.get('display_name') or c.get('name', 'Unknown')).replace(',', ' ')
            lines.append(
                f'"{name}","{cname}",{c.get("campaign_type","")},{c.get("status","")},'
                f'{c.get("impressions",0) or 0},{c.get("clicks",0) or 0},'
                f'{c.get("ctr",0) or 0:.2f},{c.get("cpc",0) or 0:.2f},'
                f'{c.get("cost_usd",0) or 0:.2f},{c.get("engagements",0) or 0}'
            )
    from flask import Response
    return Response(
        '\n'.join(lines),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=bulk_export.csv'}
    )


# ─── API: Trends with Date Range ─────────────────────────────────

@app.route('/api/trends')
def api_trends():
    """Return trend data, optionally filtered by date range."""
    trends = _get_trend_data_from_reports()
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    if start or end:
        filtered = []
        for t in trends:
            label = t.get('label', '')
            if start and label < start:
                continue
            if end and label > end:
                continue
            filtered.append(t)
        return jsonify(filtered)
    return jsonify(trends)


@app.route('/api/trends-csv')
def api_trends_csv():
    """Export trend data as CSV."""
    trends = _get_trend_data_from_reports()
    lines = ['Report,Campaigns,Impressions,Clicks,CTR,Spend']
    for t in trends:
        lines.append(f'"{t["label"]}",{t["campaigns"]},{t["impressions"]},{t["clicks"]},{t["ctr"]},{t["spend"]}')
    from flask import Response
    return Response(
        '\n'.join(lines),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=trends_export.csv'}
    )


# ─── API: Notification Center ────────────────────────────────────

@app.route('/api/notifications')
def api_notifications():
    return jsonify(_notifications[:30])


@app.route('/api/notifications/read', methods=['POST'])
def mark_notifications_read():
    for n in _notifications:
        n['read'] = True
    return jsonify({'ok': True})


@app.route('/api/notifications/clear', methods=['POST'])
def clear_notifications():
    _notifications.clear()
    return jsonify({'ok': True})


# ─── API: Global Search ─────────────────────────────────────────

@app.route('/api/search')
def api_search():
    """Search reports and campaigns."""
    q = request.args.get('q', '').lower().strip()
    if not q or len(q) < 2:
        return jsonify([])

    results = []
    # Search reports
    for r in _get_reports_list()[:20]:
        if q in r['name'].lower():
            results.append({
                'type': 'report',
                'title': r['name'],
                'subtitle': r.get('date', ''),
                'url': url_for('view_report', report_name=r['name']),
            })

    # Search campaigns within latest report
    _, latest = _get_latest_report_data()
    if latest:
        for c in latest.get('campaigns', []):
            name = c.get('display_name') or c.get('name', '')
            if q in name.lower():
                results.append({
                    'type': 'campaign',
                    'title': name,
                    'subtitle': f"CTR: {c.get('ctr', 0):.2f}% | Spend: ${c.get('cost_usd', 0):,.0f}",
                    'url': '#',
                })

    # Search pages
    pages = [
        ('Dashboard', url_for('dashboard'), 'home overview'),
        ('Generate Report', url_for('generate'), 'create new report'),
        ('Trends', url_for('trends_page'), 'historical trends charts'),
        ('Compare', url_for('compare_page'), 'compare reports side by side'),
        ('Schedules', url_for('schedule_page'), 'schedule automated reports'),
        ('Alerts', url_for('alerts_page'), 'alert notifications'),
        ('Settings', url_for('settings'), 'configuration api credentials'),
        ('Glossary', url_for('glossary_page'), 'help definitions metrics'),
        ('Activity Log', url_for('activity_page'), 'activity history'),
        ('Templates', url_for('templates_page'), 'report templates presets'),
    ]
    for title, url, keywords in pages:
        if q in title.lower() or q in keywords:
            results.append({'type': 'page', 'title': title, 'subtitle': 'Page', 'url': url})

    return jsonify(results[:15])


# ─── API: Download Report as ZIP ──────────────────────────────────

@app.route('/api/download-zip/<report_name>')
def download_zip(report_name):
    """Bundle all report files into a ZIP for download."""
    import zipfile
    import io
    buf = io.BytesIO()
    found = False
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for ext in ['.pptx', '.json', '.html', '.pdf', '.csv']:
            path = OUTPUT_DIR / f"{report_name}{ext}"
            if path.is_file():
                zf.write(str(path), f"{report_name}{ext}")
                found = True
    if not found:
        return jsonify({'error': 'No files found'}), 404
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{report_name}.zip", mimetype='application/zip')


# ─── API: Reset Settings to Defaults ─────────────────────────────

@app.route('/api/reset-settings', methods=['POST'])
def reset_settings():
    defaults = {
        'LINKEDIN_ACCESS_TOKEN': '', 'LINKEDIN_ACCOUNT_ID': '',
        'LINKEDIN_CLIENT_ID': '', 'LINKEDIN_CLIENT_SECRET': '', 'LINKEDIN_REFRESH_TOKEN': '',
        'AI_INSIGHTS_ENABLED': 'true', 'OLLAMA_ENABLED': 'true',
        'OLLAMA_MODEL': 'llama3.1', 'OLLAMA_BASE_URL': 'http://localhost:11434',
        'ANTHROPIC_API_KEY': '', 'OPENAI_API_KEY': '',
        'EMAIL_SMTP_HOST': 'smtp.gmail.com', 'EMAIL_SMTP_PORT': '587',
        'EMAIL_SENDER': '', 'EMAIL_PASSWORD': '', 'REPORT_RECIPIENTS': '',
        'SLACK_WEBHOOK_URL': '', 'BRAND_NAME': 'LinkedIn Report Automation',
        'COMPANY_NAME': '', 'THEME': 'linkedin', 'WEBHOOK_API_KEY': '',
    }
    _save_env(defaults)
    _log_activity('Settings reset', 'All settings reset to defaults')
    return jsonify({'ok': True, 'message': 'Settings reset to defaults'})


# ─── Routes: Report Rename ────────────────────────────────────────

@app.route('/api/rename-report', methods=['POST'])
def rename_report():
    old_name = request.json.get('old_name', '')
    new_name = request.json.get('new_name', '').strip()
    new_name = "".join(c for c in new_name if c.isalnum() or c in ' _-').strip().replace(' ', '_')
    if not old_name or not new_name:
        return jsonify({'ok': False, 'message': 'Both old and new names required'})
    if old_name == new_name:
        return jsonify({'ok': False, 'message': 'Names are the same'})

    renamed = []
    for ext in ['.pptx', '.json', '.html', '.pdf', '.csv']:
        old_path = OUTPUT_DIR / f"{old_name}{ext}"
        new_path = OUTPUT_DIR / f"{new_name}{ext}"
        if old_path.is_file():
            old_path.rename(new_path)
            renamed.append(ext)

    if renamed:
        _push_undo('rename_report', {'old_name': old_name, 'new_name': new_name})
        _log_activity('Report renamed', f'{old_name} -> {new_name}')
        return jsonify({'ok': True, 'renamed': renamed, 'new_name': new_name})
    return jsonify({'ok': False, 'message': 'No files found'}), 404


# ─── Routes: Duplicate Report ─────────────────────────────────────

@app.route('/api/duplicate-report/<report_name>', methods=['POST'])
def duplicate_report(report_name):
    import shutil
    ts = datetime.now().strftime('%H%M%S')
    new_name = f"{report_name}_copy_{ts}"
    copied = []
    for ext in ['.pptx', '.json', '.html', '.pdf']:
        src = OUTPUT_DIR / f"{report_name}{ext}"
        dst = OUTPUT_DIR / f"{new_name}{ext}"
        if src.is_file():
            shutil.copy2(str(src), str(dst))
            copied.append(ext)

    if copied:
        _log_activity('Report duplicated', f'{report_name} -> {new_name}')
        return jsonify({'ok': True, 'new_name': new_name, 'copied': copied})
    return jsonify({'ok': False, 'message': 'No files found'}), 404


# ─── Routes: ROI Calculator ──────────────────────────────────────

@app.route('/roi/<report_name>')
def roi_calculator(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))
    campaigns = data.get('campaigns', [])
    agg = _aggregate_campaigns(campaigns)
    return render_template('roi.html', report_name=report_name,
                           campaigns=campaigns, agg=agg)


# ─── Routes: Budget Pacing ───────────────────────────────────────

@app.route('/pacing/<report_name>')
def budget_pacing(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))
    campaigns = data.get('campaigns', [])
    agg = _aggregate_campaigns(campaigns)
    return render_template('pacing.html', report_name=report_name,
                           campaigns=campaigns, agg=agg)


# ─── Routes: Creative Gallery ────────────────────────────────────

@app.route('/creatives/<report_name>')
def creative_gallery(report_name):
    data = _get_report_data(report_name)
    if not data:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard'))
    campaigns = data.get('campaigns', [])
    creatives = []
    for c in campaigns:
        for cr in c.get('creatives', []):
            cr['campaign_name'] = c.get('display_name', c.get('name', 'Unknown'))
            cr['campaign_id'] = c.get('id', '')
            creatives.append(cr)
    return render_template('creatives.html', report_name=report_name,
                           creatives=creatives, campaigns=campaigns)


# ─── Routes: API Documentation ───────────────────────────────────

@app.route('/api-docs')
def api_docs():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        func = app.view_functions.get(rule.endpoint)
        doc = func.__doc__.strip() if func and func.__doc__ else ''
        routes.append({
            'path': rule.rule,
            'methods': sorted([m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]),
            'endpoint': rule.endpoint,
            'doc': doc,
        })
    routes.sort(key=lambda r: r['path'])
    return render_template('api_docs.html', routes=routes)


# ─── API: Report Comments ────────────────────────────────────────

@app.route('/api/comments/<report_name>', methods=['GET', 'POST'])
def report_comments(report_name):
    if request.method == 'POST':
        text = request.json.get('text', '').strip()
        author = request.json.get('author', 'Anonymous').strip()
        parent_id = request.json.get('parent_id')
        if not text:
            return jsonify({'ok': False, 'message': 'Comment text required'})
        comment = {
            'id': f"cmt_{int(time.time())}_{len(_comments.get(report_name, []))}",
            'text': text,
            'author': author,
            'time': datetime.now().strftime('%d %b %Y, %I:%M %p'),
            'parent_id': parent_id,
            'replies': [],
        }
        if report_name not in _comments:
            _comments[report_name] = []
        if parent_id:
            for c in _comments[report_name]:
                if c['id'] == parent_id:
                    c['replies'].append(comment)
                    break
        else:
            _comments[report_name].insert(0, comment)
        _log_activity('Comment added', f'{report_name}: {text[:40]}', notify=False)
        return jsonify({'ok': True, 'comment': comment})
    return jsonify(_comments.get(report_name, []))


@app.route('/api/comments/<report_name>/<comment_id>', methods=['DELETE'])
def delete_comment(report_name, comment_id):
    if report_name in _comments:
        _comments[report_name] = [c for c in _comments[report_name] if c['id'] != comment_id]
        for c in _comments[report_name]:
            c['replies'] = [r for r in c.get('replies', []) if r['id'] != comment_id]
    return jsonify({'ok': True})


# ─── API: Report Versioning ──────────────────────────────────────

@app.route('/api/versions/<report_name>')
def report_versions(report_name):
    return jsonify(_versions.get(report_name, []))


# ─── API: Account Profiles ───────────────────────────────────────

@app.route('/api/profiles', methods=['GET', 'POST'])
def account_profiles():
    if request.method == 'POST':
        profile = {
            'id': f"prof_{int(time.time())}",
            'name': request.json.get('name', 'Default'),
            'access_token': request.json.get('access_token', ''),
            'account_id': request.json.get('account_id', ''),
            'created': datetime.now().strftime('%d %b %Y'),
        }
        _account_profiles.append(profile)
        return jsonify({'ok': True, 'profile': profile})
    return jsonify(_account_profiles)


@app.route('/api/profiles/<profile_id>/activate', methods=['POST'])
def activate_profile(profile_id):
    for p in _account_profiles:
        if p['id'] == profile_id:
            env = _load_env()
            env['LINKEDIN_ACCESS_TOKEN'] = p['access_token']
            env['LINKEDIN_ACCOUNT_ID'] = p['account_id']
            _save_env(env)
            os.environ['LINKEDIN_ACCESS_TOKEN'] = p['access_token']
            os.environ['LINKEDIN_ACCOUNT_ID'] = p['account_id']
            _log_activity('Profile activated', p['name'])
            return jsonify({'ok': True, 'message': f'Switched to profile: {p["name"]}'})
    return jsonify({'ok': False, 'message': 'Profile not found'}), 404


@app.route('/api/profiles/<profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    global _account_profiles
    _account_profiles = [p for p in _account_profiles if p['id'] != profile_id]
    return jsonify({'ok': True})


# ─── API: Data Retention ─────────────────────────────────────────

@app.route('/api/data-retention', methods=['POST'])
def apply_data_retention():
    """Delete reports older than N days."""
    try:
        days = int(request.json.get('days', 90))
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'error': 'Invalid days value'}), 400
    if days < 1:
        return jsonify({'ok': False, 'error': 'Days must be at least 1'}), 400
    cutoff = time.time() - (days * 86400)
    deleted = 0
    if OUTPUT_DIR.is_dir():
        for f in OUTPUT_DIR.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
    _log_activity('Data retention applied', f'Deleted {deleted} files older than {days} days')
    return jsonify({'ok': True, 'deleted': deleted, 'days': days})


# ─── API: Report Sharing (Public Links) ──────────────────────────

_shared_links = {}

@app.route('/api/share/<report_name>', methods=['POST'])
def create_share_link(report_name):
    """Generate a shareable token for a report."""
    import hashlib
    token = hashlib.sha256(f"{report_name}_{time.time()}".encode()).hexdigest()[:16]
    _shared_links[token] = {
        'report_name': report_name,
        'created': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'expires': None,
    }
    _log_activity('Report shared', f'{report_name} (token: {token[:8]}...)')
    return jsonify({
        'ok': True,
        'token': token,
        'url': url_for('view_shared_report', token=token, _external=True),
    })


@app.route('/shared/<token>')
def view_shared_report(token):
    link = _shared_links.get(token)
    if not link:
        flash('Invalid or expired share link.', 'error')
        return redirect(url_for('dashboard'))
    report_name = link['report_name']
    data = _get_report_data(report_name)
    if not data:
        flash('Report not found.', 'error')
        return redirect(url_for('dashboard'))
    campaigns = data.get('campaigns', [])
    agg = _aggregate_campaigns(campaigns)
    report_date = data.get('report_date', 'N/A')
    return render_template('shared_report.html',
                           report_name=report_name, report_date=report_date,
                           campaigns=campaigns, agg=agg, shared=True)


# ─── API: Undo Operations ────────────────────────────────────────

def _push_undo(action, data):
    _undo_stack.append({
        'action': action,
        'data': data,
        'time': datetime.now().strftime('%I:%M %p'),
    })
    if len(_undo_stack) > 20:
        _undo_stack.pop(0)


@app.route('/api/undo', methods=['POST'])
def undo_last():
    if not _undo_stack:
        return jsonify({'ok': False, 'message': 'Nothing to undo'})
    entry = _undo_stack.pop()
    action = entry['action']

    if action == 'delete_report':
        # Can't truly undo a file delete, but acknowledge
        return jsonify({'ok': False, 'message': 'File deletions cannot be undone'})
    elif action == 'rename_report':
        old_name = entry['data']['new_name']
        new_name = entry['data']['old_name']
        for ext in ['.pptx', '.json', '.html', '.pdf', '.csv']:
            old_path = OUTPUT_DIR / f"{old_name}{ext}"
            new_path = OUTPUT_DIR / f"{new_name}{ext}"
            if old_path.is_file():
                old_path.rename(new_path)
        return jsonify({'ok': True, 'message': f'Undid rename: restored to {new_name}'})
    elif action == 'delete_note':
        rn = entry['data']['report_name']
        note = entry['data']['note']
        if rn not in _notes:
            _notes[rn] = []
        _notes[rn].insert(0, note)
        return jsonify({'ok': True, 'message': 'Note restored'})

    return jsonify({'ok': False, 'message': f'Cannot undo action: {action}'})


@app.route('/api/undo-stack')
def undo_stack():
    return jsonify([{'action': u['action'], 'time': u['time']} for u in reversed(_undo_stack)])


# Load .env on startup
if ENV_PATH.is_file():
    try:
        from dotenv import load_dotenv
        load_dotenv(str(ENV_PATH), override=True)
    except ImportError:
        for k, v in _load_env().items():
            os.environ.setdefault(k, v)


if __name__ == '__main__':
    OUTPUT_DIR.mkdir(exist_ok=True)
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5000)))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    print(f"\n  LinkedIn Report Automation Dashboard")
    print(f"  Open http://localhost:{port} in your browser\n")
    app.run(host=host, port=port, debug=debug)
