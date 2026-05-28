"""
SQLite-based historical data storage for trend analysis.

Stores report data and campaign snapshots in a local SQLite database,
enabling historical trend queries and report retrieval.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime


class DataStore:
    """Persistent storage for report data using SQLite.

    Tables:
        reports - Stores full report snapshots (id, date, campaigns JSON,
                  aggregate metrics JSON).
        campaign_snapshots - Stores per-campaign metrics over time for
                             trend analysis.
    """

    def __init__(self, db_path='data/reports.db'):
        """Initialize the data store.

        Args:
            db_path: Path to the SQLite database file. Parent directories
                     are created automatically.
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_tables()

    def _get_conn(self):
        """Create a new database connection.

        Returns:
            sqlite3.Connection with row factory set.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create tables if they do not exist."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    campaign_count INTEGER DEFAULT 0,
                    total_impressions INTEGER DEFAULT 0,
                    total_clicks INTEGER DEFAULT 0,
                    total_spend REAL DEFAULT 0,
                    overall_ctr REAL DEFAULT 0,
                    campaigns_json TEXT,
                    metrics_json TEXT
                );

                CREATE TABLE IF NOT EXISTS campaign_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER,
                    campaign_id TEXT NOT NULL,
                    campaign_name TEXT,
                    snapshot_date TEXT NOT NULL,
                    impressions INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    engagements INTEGER DEFAULT 0,
                    spend REAL DEFAULT 0,
                    ctr REAL DEFAULT 0,
                    cpc REAL DEFAULT 0,
                    engagement_rate REAL DEFAULT 0,
                    campaign_type TEXT,
                    status TEXT,
                    FOREIGN KEY (report_id) REFERENCES reports(id)
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_campaign
                    ON campaign_snapshots(campaign_id, snapshot_date);

                CREATE INDEX IF NOT EXISTS idx_reports_date
                    ON reports(report_date);
            """)
            conn.commit()
        finally:
            conn.close()

    def save_report(self, report_data):
        """Save a complete report to the database.

        Stores the report summary in the reports table and individual
        campaign snapshots in the campaign_snapshots table.

        Args:
            report_data: Dict with 'campaigns' list and 'report_date' string,
                         as returned by LinkedInClient.fetch_all_campaign_data().

        Returns:
            The report ID (integer) of the saved report.
        """
        campaigns = report_data.get('campaigns', [])
        report_date = report_data.get('report_date', datetime.now().strftime('%d-%m-%Y'))

        # Aggregate metrics
        total_imp = sum(c.get('impressions') or 0 for c in campaigns)
        total_clk = sum(c.get('clicks') or 0 for c in campaigns)
        total_spend = sum(c.get('cost_usd') or 0.0 for c in campaigns)
        overall_ctr = (total_clk / total_imp * 100) if total_imp else 0

        metrics = {
            'total_impressions': total_imp,
            'total_clicks': total_clk,
            'total_spend': round(total_spend, 2),
            'overall_ctr': round(overall_ctr, 2),
            'campaign_count': len(campaigns),
        }

        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """INSERT INTO reports
                   (report_date, campaign_count, total_impressions, total_clicks,
                    total_spend, overall_ctr, campaigns_json, metrics_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report_date,
                    len(campaigns),
                    total_imp,
                    total_clk,
                    round(total_spend, 2),
                    round(overall_ctr, 2),
                    json.dumps(campaigns, default=str),
                    json.dumps(metrics),
                ),
            )
            report_id = cursor.lastrowid

            # Save campaign snapshots
            for c in campaigns:
                conn.execute(
                    """INSERT INTO campaign_snapshots
                       (report_id, campaign_id, campaign_name, snapshot_date,
                        impressions, clicks, engagements, spend, ctr, cpc,
                        engagement_rate, campaign_type, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        report_id,
                        c.get('id', ''),
                        c.get('display_name', c.get('name', '')),
                        report_date,
                        c.get('impressions') or 0,
                        c.get('clicks') or 0,
                        c.get('engagements') or 0,
                        round(c.get('cost_usd') or 0, 2),
                        round(c.get('ctr') or 0, 2),
                        round(c.get('cpc') or 0, 2),
                        round(c.get('engagement_rate') or 0, 2),
                        c.get('campaign_type', ''),
                        c.get('status', ''),
                    ),
                )

            conn.commit()
            print(f"  DataStore: Saved report #{report_id} with "
                  f"{len(campaigns)} campaigns.", file=sys.stderr)
            return report_id
        finally:
            conn.close()

    def get_report(self, report_id):
        """Retrieve a report by its ID.

        Args:
            report_id: Integer report ID.

        Returns:
            Dict with report data, or None if not found.
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get('campaigns_json'):
                result['campaigns'] = json.loads(result['campaigns_json'])
            if result.get('metrics_json'):
                result['metrics'] = json.loads(result['metrics_json'])
            return result
        finally:
            conn.close()

    def get_latest_report(self):
        """Retrieve the most recent report.

        Returns:
            Dict with report data, or None if no reports exist.
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM reports ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get('campaigns_json'):
                result['campaigns'] = json.loads(result['campaigns_json'])
            if result.get('metrics_json'):
                result['metrics'] = json.loads(result['metrics_json'])
            return result
        finally:
            conn.close()

    def get_campaign_history(self, campaign_id, limit=30):
        """Get historical snapshots for a specific campaign.

        Args:
            campaign_id: The campaign ID string.
            limit: Maximum number of snapshots to return (default: 30).

        Returns:
            List of snapshot dicts, ordered by date ascending.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT * FROM campaign_snapshots
                   WHERE campaign_id = ?
                   ORDER BY snapshot_date ASC
                   LIMIT ?""",
                (campaign_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_trend(self, metric='total_impressions', limit=30):
        """Get trend data for a specific aggregate metric over time.

        Args:
            metric: Column name from the reports table. One of:
                    'total_impressions', 'total_clicks', 'total_spend',
                    'overall_ctr', 'campaign_count'.
            limit: Maximum number of data points (default: 30).

        Returns:
            List of dicts with 'date' and 'value' keys, ordered by
            date ascending.
        """
        valid_metrics = {
            'total_impressions', 'total_clicks', 'total_spend',
            'overall_ctr', 'campaign_count',
        }
        if metric not in valid_metrics:
            print(f"  Warning: Invalid metric '{metric}'. "
                  f"Valid: {', '.join(sorted(valid_metrics))}",
                  file=sys.stderr)
            return []

        conn = self._get_conn()
        try:
            rows = conn.execute(
                f"""SELECT report_date, {metric} as value
                    FROM reports
                    ORDER BY id ASC
                    LIMIT ?""",
                (limit,),
            ).fetchall()
            return [{'date': r['report_date'], 'value': r['value']} for r in rows]
        finally:
            conn.close()

    def list_reports(self, limit=20):
        """List recent reports (summary only, without full campaign JSON).

        Args:
            limit: Maximum number of reports to return (default: 20).

        Returns:
            List of dicts with report metadata.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT id, report_date, created_at, campaign_count,
                          total_impressions, total_clicks, total_spend, overall_ctr
                   FROM reports
                   ORDER BY id DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
