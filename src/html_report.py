"""
Generate an interactive HTML report with Chart.js.

Produces a single-file HTML report with an executive summary,
campaign cards, charts (bar, line, pie), interactive tooltips,
campaign filters, and a dark mode toggle.
"""

import json
import os
import sys
from datetime import datetime


def _build_chart_data(campaigns):
    """Build data structures for Chart.js charts.

    Args:
        campaigns: List of campaign dicts.

    Returns:
        Dict with chart configuration data.
    """
    labels = []
    impressions = []
    clicks = []
    ctrs = []
    spends = []

    for c in campaigns:
        labels.append(c.get('display_name', c.get('name', 'Unknown'))[:30])
        impressions.append(c.get('impressions') or 0)
        clicks.append(c.get('clicks') or 0)
        ctrs.append(round(c.get('ctr') or 0, 2))
        spends.append(round(c.get('cost_usd') or 0, 2))

    # Campaign type distribution for pie chart
    type_counts = {}
    for c in campaigns:
        ct = c.get('campaign_type', 'Other')
        type_counts[ct] = type_counts.get(ct, 0) + 1

    return {
        'labels': labels,
        'impressions': impressions,
        'clicks': clicks,
        'ctrs': ctrs,
        'spends': spends,
        'type_labels': list(type_counts.keys()),
        'type_counts': list(type_counts.values()),
    }


def _build_monthly_chart_data(campaigns):
    """Aggregate monthly trend data across campaigns.

    Args:
        campaigns: List of campaign dicts with 'monthly_trends'.

    Returns:
        Dict with monthly labels, impressions, clicks, and spend arrays.
    """
    monthly = {}
    for c in campaigns:
        for m in c.get('monthly_trends', []):
            label = m.get('month', 'Unknown')
            if label not in monthly:
                monthly[label] = {'impressions': 0, 'clicks': 0, 'spend': 0}
            monthly[label]['impressions'] += m.get('impressions', 0)
            monthly[label]['clicks'] += m.get('clicks', 0)
            monthly[label]['spend'] += m.get('cost', 0)

    labels = list(monthly.keys())
    return {
        'labels': labels,
        'impressions': [monthly[l]['impressions'] for l in labels],
        'clicks': [monthly[l]['clicks'] for l in labels],
        'spend': [round(monthly[l]['spend'], 2) for l in labels],
    }


def generate_html_report(report_data, output_path=None):
    """Generate a single-file interactive HTML report.

    Creates a self-contained HTML file with embedded Chart.js charts,
    campaign cards, dark mode toggle, and campaign type filters.

    Args:
        report_data: Dict with 'campaigns' list and 'report_date' string,
                     as returned by LinkedInClient.fetch_all_campaign_data().
        output_path: Output file path. If None, generates a path in the
                     output/ directory.

    Returns:
        The path to the generated HTML file.
    """
    campaigns = report_data.get('campaigns', [])
    report_date = report_data.get('report_date', datetime.now().strftime('%d-%m-%Y'))

    if output_path is None:
        os.makedirs('output', exist_ok=True)
        timestamp = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        output_path = os.path.join('output', f'LinkedIn_Report_{timestamp}.html')

    # Aggregate metrics
    total_imp = sum(c.get('impressions') or 0 for c in campaigns)
    total_clk = sum(c.get('clicks') or 0 for c in campaigns)
    total_eng = sum(c.get('engagements') or 0 for c in campaigns)
    total_spend = sum(c.get('cost_usd') or 0.0 for c in campaigns)
    overall_ctr = (total_clk / total_imp * 100) if total_imp else 0
    overall_cpc = (total_spend / total_clk) if total_clk else 0

    chart_data = _build_chart_data(campaigns)
    monthly_data = _build_monthly_chart_data(campaigns)

    # Get unique campaign types for filter
    campaign_types = sorted(set(c.get('campaign_type', 'Other') for c in campaigns))

    # Build campaign cards HTML
    campaign_cards_html = ''
    for c in campaigns:
        imp = c.get('impressions') or 0
        clk = c.get('clicks') or 0
        ctr = c.get('ctr') or 0
        spend = c.get('cost_usd') or 0
        eng = c.get('engagements') or 0
        cpc = c.get('cpc') or 0
        camp_type = c.get('campaign_type', 'Other')
        geo = c.get('geo_display', 'N/A')
        name = c.get('display_name', c.get('name', 'Unknown'))

        campaign_cards_html += f"""
      <div class="campaign-card" data-type="{camp_type}">
        <div class="card-header">
          <h3>{name}</h3>
          <span class="badge">{camp_type}</span>
        </div>
        <div class="card-meta">{geo} | Status: {c.get('status', 'N/A')}</div>
        <div class="card-metrics">
          <div class="metric"><span class="metric-value">{imp:,}</span><span class="metric-label">Impressions</span></div>
          <div class="metric"><span class="metric-value">{clk:,}</span><span class="metric-label">Clicks</span></div>
          <div class="metric"><span class="metric-value">{ctr:.2f}%</span><span class="metric-label">CTR</span></div>
          <div class="metric"><span class="metric-value">${spend:,.2f}</span><span class="metric-label">Spend</span></div>
          <div class="metric"><span class="metric-value">{eng:,}</span><span class="metric-label">Engagements</span></div>
          <div class="metric"><span class="metric-value">${cpc:.2f}</span><span class="metric-label">CPC</span></div>
        </div>
      </div>"""

    # Filter buttons HTML
    filter_buttons = '<button class="filter-btn active" data-filter="all">All</button>'
    for ct in campaign_types:
        filter_buttons += f'<button class="filter-btn" data-filter="{ct}">{ct}</button>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LinkedIn Campaign Report - {report_date}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #f5f7fa; --card-bg: #ffffff; --text: #333333; --text-muted: #666666;
    --primary: #0A66C2; --accent: #004B87; --border: #e0e0e0;
    --success: #057A42; --danger: #CC1C39;
  }}
  .dark {{
    --bg: #0f0f1a; --card-bg: #1a1a2e; --text: #e0e0e0; --text-muted: #aaaaaa;
    --primary: #4da3ff; --accent: #6db8ff; --border: #333355;
    --success: #00d27a; --danger: #e74c3c;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Calibri, 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--text); transition: background 0.3s, color 0.3s; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
  .header {{ background: var(--primary); color: #fff; padding: 24px 32px; border-radius: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
  .header h1 {{ font-size: 24px; }}
  .header .date {{ font-size: 14px; opacity: 0.85; }}
  .dark-toggle {{ background: rgba(255,255,255,0.2); border: none; color: #fff; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }}
  .dark-toggle:hover {{ background: rgba(255,255,255,0.3); }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .kpi-card {{ background: var(--card-bg); border-radius: 10px; padding: 20px; text-align: center; border: 1px solid var(--border); }}
  .kpi-card .kpi-value {{ font-size: 28px; font-weight: 700; color: var(--primary); }}
  .kpi-card .kpi-label {{ font-size: 13px; color: var(--text-muted); margin-top: 4px; }}
  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
  .chart-container {{ background: var(--card-bg); border-radius: 10px; padding: 20px; border: 1px solid var(--border); }}
  .chart-container h2 {{ font-size: 16px; margin-bottom: 12px; color: var(--primary); }}
  .chart-container canvas {{ max-height: 300px; }}
  .filters {{ margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; }}
  .filter-btn {{ padding: 6px 14px; border: 1px solid var(--border); border-radius: 20px; background: var(--card-bg); color: var(--text); cursor: pointer; font-size: 13px; }}
  .filter-btn.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
  .campaign-card {{ background: var(--card-bg); border-radius: 10px; padding: 20px; margin-bottom: 16px; border: 1px solid var(--border); }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
  .card-header h3 {{ font-size: 16px; color: var(--text); }}
  .badge {{ background: var(--primary); color: #fff; padding: 3px 10px; border-radius: 12px; font-size: 11px; }}
  .card-meta {{ font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }}
  .card-metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; }}
  .metric {{ text-align: center; }}
  .metric-value {{ display: block; font-size: 18px; font-weight: 600; color: var(--primary); }}
  .metric-label {{ display: block; font-size: 11px; color: var(--text-muted); }}
  .footer {{ text-align: center; padding: 20px; font-size: 12px; color: var(--text-muted); }}
  @media (max-width: 768px) {{
    .charts-grid {{ grid-template-columns: 1fr; }}
    .header {{ flex-direction: column; gap: 12px; text-align: center; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>LinkedIn Campaign Report</h1>
      <div class="date">Report Date: {report_date} | {len(campaigns)} Campaigns</div>
    </div>
    <button class="dark-toggle" onclick="document.body.classList.toggle('dark')">Toggle Dark Mode</button>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-value">{total_imp:,}</div><div class="kpi-label">Impressions</div></div>
    <div class="kpi-card"><div class="kpi-value">{total_clk:,}</div><div class="kpi-label">Clicks</div></div>
    <div class="kpi-card"><div class="kpi-value">{overall_ctr:.2f}%</div><div class="kpi-label">CTR</div></div>
    <div class="kpi-card"><div class="kpi-value">${total_spend:,.2f}</div><div class="kpi-label">Total Spend</div></div>
    <div class="kpi-card"><div class="kpi-value">${overall_cpc:.2f}</div><div class="kpi-label">Avg CPC</div></div>
    <div class="kpi-card"><div class="kpi-value">{total_eng:,}</div><div class="kpi-label">Engagements</div></div>
  </div>

  <div class="charts-grid">
    <div class="chart-container">
      <h2>Impressions & Clicks by Campaign</h2>
      <canvas id="barChart"></canvas>
    </div>
    <div class="chart-container">
      <h2>CTR by Campaign</h2>
      <canvas id="ctrChart"></canvas>
    </div>
    <div class="chart-container">
      <h2>Monthly Trends</h2>
      <canvas id="lineChart"></canvas>
    </div>
    <div class="chart-container">
      <h2>Campaign Type Distribution</h2>
      <canvas id="pieChart"></canvas>
    </div>
  </div>

  <h2 style="margin-bottom: 12px; color: var(--primary);">Campaigns</h2>
  <div class="filters">
    {filter_buttons}
  </div>
  <div id="campaignList">
    {campaign_cards_html}
  </div>

  <div class="footer">Generated with LinkedIn Report Automation</div>
</div>

<script>
const chartColors = ['#0A66C2','#004B87','#F5A623','#057A42','#CC1C39','#8B5CF6','#06B6D4','#F97316'];

// Bar Chart: Impressions & Clicks
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_data['labels'])},
    datasets: [
      {{ label: 'Impressions', data: {json.dumps(chart_data['impressions'])}, backgroundColor: '#0A66C2' }},
      {{ label: 'Clicks', data: {json.dumps(chart_data['clicks'])}, backgroundColor: '#F5A623' }}
    ]
  }},
  options: {{ responsive: true, plugins: {{ legend: {{ position: 'top' }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});

// CTR Bar Chart
new Chart(document.getElementById('ctrChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_data['labels'])},
    datasets: [{{ label: 'CTR (%)', data: {json.dumps(chart_data['ctrs'])}, backgroundColor: '#057A42' }}]
  }},
  options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
}});

// Monthly Line Chart
new Chart(document.getElementById('lineChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(monthly_data['labels'])},
    datasets: [
      {{ label: 'Impressions', data: {json.dumps(monthly_data['impressions'])}, borderColor: '#0A66C2', fill: false, tension: 0.3 }},
      {{ label: 'Clicks', data: {json.dumps(monthly_data['clicks'])}, borderColor: '#F5A623', fill: false, tension: 0.3 }}
    ]
  }},
  options: {{ responsive: true }}
}});

// Pie Chart: Campaign Types
new Chart(document.getElementById('pieChart'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(chart_data['type_labels'])},
    datasets: [{{ data: {json.dumps(chart_data['type_counts'])}, backgroundColor: chartColors.slice(0, {len(chart_data['type_labels'])}) }}]
  }},
  options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
}});

// Filter functionality
document.querySelectorAll('.filter-btn').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    btn.classList.add('active');
    var filter = btn.getAttribute('data-filter');
    document.querySelectorAll('.campaign-card').forEach(function(card) {{
      if (filter === 'all' || card.getAttribute('data-type') === filter) {{
        card.style.display = '';
      }} else {{
        card.style.display = 'none';
      }}
    }});
  }});
}});
</script>
</body>
</html>"""

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  HTML report generated: {output_path}", file=sys.stderr)
        return output_path
    except Exception as e:
        print(f"  Warning: HTML report generation failed: {e}", file=sys.stderr)
        return ''
