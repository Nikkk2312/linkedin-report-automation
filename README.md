<p align="center">
  <img src="assets/logo.png" alt="LinkedIn Report Automation" width="180"/>
</p>

<h1 align="center">LinkedIn Report Automation</h1>

<p align="center">
  <strong>Turn LinkedIn Ad data into professional reports with a single click.</strong><br/>
  Full-stack analytics dashboard + automated PowerPoint generation + AI-powered insights.
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white" alt="Python 3.9+"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-Dashboard-000000?logo=flask&logoColor=white" alt="Flask"></a>
  <a href="https://learn.microsoft.com/en-us/linkedin/marketing/"><img src="https://img.shields.io/badge/LinkedIn-Marketing_API-0A66C2?logo=linkedin&logoColor=white" alt="LinkedIn API"></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/AI-Ollama%20%7C%20Claude%20%7C%20OpenAI-blueviolet" alt="AI Insights"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="License MIT"></a>
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="Version 2.0.0">
  <a href="https://linkedin-report-automation.onrender.com"><img src="https://img.shields.io/badge/live%20demo-online-brightgreen" alt="Live Demo"></a>
</p>

<p align="center">
  <strong>▶ <a href="https://linkedin-report-automation.onrender.com">Try the live demo</a></strong> — loads instantly with a sample report (15 campaigns, 90+ metrics). No login, no setup.<br/>
  <a href="https://codespaces.new/Nikkk2312/linkedin-report-automation">Open in Codespaces</a> &bull;
  <a href="https://render.com/deploy?repo=https://github.com/Nikkk2312/linkedin-report-automation">Deploy your own</a> &bull;
  <code>docker compose up</code>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="#-web-dashboard">Dashboard</a> &bull;
  <a href="#-features">Features</a> &bull;
  <a href="#-deploy-free">Deploy Free</a> &bull;
  <a href="#-architecture">Architecture</a> &bull;
  <a href="#-api-reference">API</a>
</p>

---

## What is this?

A self-hosted analytics platform that connects to the **LinkedIn Marketing API**, fetches 90+ metrics across your ad campaigns, and gives you:

- A **24-page interactive web dashboard** with charts, filters, and real-time analysis
- **Branded PowerPoint reports** (40-60+ slides per report) generated automatically
- **AI-powered insights** via Ollama (free/local), Claude, or OpenAI
- **Demographics analysis** across 8 dimensions (job titles, industries, seniority, geography, etc.)
- **One-click export** to Google Sheets, Google Slides, PDF, and HTML
- **Automated delivery** via email and Slack

No paid SaaS. No vendor lock-in. Your data stays on your infrastructure.

---

## Web Dashboard

The built-in Flask dashboard provides a complete analytics interface at `http://localhost:5000`:

| Page | What it does |
|---|---|
| **Dashboard** | KPI cards, sparklines, top performers, recent reports |
| **Generate Report** | Multi-step wizard: connect API, pick date range, select campaigns, choose options |
| **Campaign Detail** | Deep-dive into any campaign: health score, radar chart, engagement breakdown, demographics |
| **Compare** | Side-by-side comparison of up to 5 reports with bar charts |
| **Demographics** | 11 demographic pivots with distribution charts and CSV export |
| **Trends** | Historical multi-metric analysis with period-over-period comparison |
| **AI Insights** | On-demand strategic insights, budget optimization, audience targeting, A/B tests |
| **Creatives** | Gallery view of all creatives with sortable performance metrics |
| **Budget & Cost** | Spend analysis, CPC vs benchmarks, efficiency scoring |
| **ROI Calculator** | Revenue settings, per-campaign ROI/ROAS breakdown |
| **Funnel** | Conversion funnel visualization: Impressions -> Clicks -> Engagements -> Leads |
| **Pacing** | Budget pacing analyzer with gauge charts and projections |
| **What-If Simulator** | Interactive budget sliders with real-time projection updates |
| **Alerts** | Configure performance alerts with email/Slack notifications |
| **Schedules** | Set up automated daily/weekly/monthly report generation |
| **Report Templates** | Pre-built templates for quick report generation |
| **Report Viewer** | Full report analysis with toggleable sections, comments, version history |
| **Shared Reports** | Read-only shareable report links |
| **Activity Log** | Timeline of all actions and report generations |
| **Settings** | LinkedIn API, AI provider, email/Slack, branding, account profiles |
| **API Docs** | Interactive API endpoint documentation |
| **Glossary** | Searchable reference for all metrics, benchmarks, and features |

---

## Features

### Report Generation
- **40-60+ professionally designed slides** per PowerPoint report
- Executive Summary with KPI cards
- Campaign Overview table with color-coded CTR benchmarking
- Impressions, cost, and engagement comparison charts
- Creative performance rankings with image thumbnails
- **8 demographic slides per campaign** (Companies, Industries, Job Titles, Job Functions, Seniority, Company Size, Geography, Device)
- Aggregate demographics across all campaigns
- Monthly trend charts and period-over-period comparison
- Viral performance, lead gen funnel, messaging, and document ad analytics
- Video analytics (views, completion rates, view-through rate)
- 2026 industry benchmarks by format and industry
- A/B test results with statistical significance

### AI-Powered Analytics
- **Ollama** (free, local, private) - no API key needed
- **Claude** and **OpenAI** as cloud fallbacks
- Automatic fallback chain: Ollama -> Claude -> OpenAI -> rule-based analysis
- Strategic insights and executive summaries
- Budget optimization recommendations
- Audience targeting suggestions
- Creative performance analysis

### Data & API
- **90+ LinkedIn API metrics** fetched across 5 API batches
- **30+ derived metrics** (viral amplification, frequency, video completion rate, etc.)
- Full demographic name resolution via LinkedIn API
- LinkedIn Industry Taxonomy v2 (434 industries)
- Batch API calls with rate limiting and automatic retries
- Multi-account support

### Integrations
| Integration | Purpose |
|---|---|
| Google Sheets | Formatted demographic worksheets, auto-shared |
| Google Slides | Full presentation export |
| PDF Export | Via LibreOffice (headless) |
| HTML Reports | Self-contained interactive reports with Chart.js |
| Email (SMTP) | Report delivery with formatted HTML summary |
| Slack | KPI highlights and download links via webhook |
| Webhooks | Custom callbacks for external systems |
| n8n | Workflow automation with web form trigger |

### Dashboard Analytics
- Campaign health scoring (composite of CTR, CPC, Engagement)
- Budget pacing with gauge charts and projections
- What-if budget simulator with interactive sliders
- ROI/ROAS calculator with per-campaign breakdown
- Conversion funnel visualization
- Performance alert configuration
- Scheduled report automation
- Report version history and comments
- Dark mode support

---

## Quick Start

### Prerequisites

- **Python 3.9+**
- A **LinkedIn Marketing API** access token ([Get one here](https://www.linkedin.com/developers/apps))

### 1. Clone and install

```bash
git clone https://github.com/Nikkk2312/linkedin-report-automation.git
cd linkedin-report-automation
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your LinkedIn API token and account ID
```

Or run the **guided setup wizard**:
```bash
python -m src.setup_wizard
```

### 3. Launch the dashboard

```bash
python app.py
# Open http://localhost:5000
```

### 4. Generate your first report

Navigate to **Generate Report** in the dashboard, enter your credentials, select campaigns, and click generate. Your branded PPTX will be ready in seconds.

### Alternative: CLI mode

```bash
# All active campaigns
python run.py --env .env --campaigns active

# Specific campaigns
python run.py --env .env --campaigns 12345,67890

# With PDF export
python run.py --env .env --campaigns active --pdf
```

### Alternative: n8n workflow

```bash
bash start-n8n.sh
# Open http://localhost:5678/webhook/linkedin-report-v2
```

---

## Deploy Free

### Render.com (Recommended)

Deploy the dashboard to Render's free tier with one click:

1. Fork this repository
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your forked repo
4. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. Add your environment variables in the Render dashboard (see `.env.example`)

### Docker

```bash
docker compose up --build
# Dashboard: http://localhost:5000
# n8n:       http://localhost:5678
```

### Railway / Fly.io

Both support Python apps out of the box. Use the included `Procfile`:

```bash
# Railway
railway init && railway up

# Fly.io
fly launch && fly deploy
```

---

## Architecture

```
                    LinkedIn Report Automation v2.0

  +---------------------------------------------------------------+
  |                     Flask Web Dashboard                        |
  |               24 pages - http://localhost:5000                 |
  |                                                                |
  |  Dashboard | Generate | Campaigns | Compare | Demographics     |
  |  Trends | Insights | Creatives | Budget | ROI | Funnel        |
  |  Pacing | Alerts | Schedules | Settings | API Docs            |
  +-------+-------------------------------------------------------+
          |
          v
  +-------+-------------------------------------------------------+
  |                      Python Backend                            |
  |                                                                |
  |  linkedin_client.py     report_generator.py    ollama_insights |
  |  (90+ metrics,          (40-60+ slides,        (Ollama/Claude/ |
  |   5 API batches)         demographics)          OpenAI)        |
  |                                                                |
  |  sheets_uploader.py     email_sender.py        slack_notifier  |
  |  slides_exporter.py     pdf_exporter.py        ab_test_analyzer|
  |  budget_optimizer.py    audience_recommender   data_store.py   |
  |  token_refresh.py       scheduled_report.py    archiver.py     |
  +-------+-------------------------------------------------------+
          |
          v
  +-------+-------------------------------------------------------+
  |                     External Services                          |
  |                                                                |
  |  LinkedIn Marketing API    Google Sheets/Slides/Drive          |
  |  Ollama (local AI)         SMTP Email                          |
  |  Claude / OpenAI API       Slack Webhooks                      |
  |  SQLite (historical)       n8n (optional workflow)             |
  +---------------------------------------------------------------+
```

---

## Configuration

All configuration via environment variables. Copy `.env.example` to `.env`.

<details>
<summary><strong>Full configuration reference (click to expand)</strong></summary>

| Variable | Description | Required |
|---|---|---|
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn API OAuth token | Yes |
| `LINKEDIN_ACCOUNT_ID` | LinkedIn Ad Account ID | Yes |
| `LINKEDIN_CLIENT_ID` | LinkedIn App Client ID | No |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn App Client Secret | No |
| `LINKEDIN_REFRESH_TOKEN` | LinkedIn OAuth Refresh Token | No |
| `LINKEDIN_ACCOUNT_IDS` | Comma-separated account IDs (multi-account) | No |
| `OLLAMA_ENABLED` | Enable Ollama AI insights | No |
| `OLLAMA_MODEL` | Ollama model name | No |
| `OLLAMA_BASE_URL` | Ollama server URL | No |
| `ANTHROPIC_API_KEY` | Anthropic API key (Claude) | No |
| `OPENAI_API_KEY` | OpenAI API key | No |
| `EMAIL_DELIVERY` | Enable email delivery | No |
| `EMAIL_SMTP_HOST` | SMTP server hostname | No |
| `EMAIL_SMTP_PORT` | SMTP server port | No |
| `EMAIL_SENDER` | Sender email address | No |
| `EMAIL_PASSWORD` | Sender email password | No |
| `EMAIL_RECIPIENTS` | Comma-separated recipient emails | No |
| `SLACK_NOTIFICATIONS` | Enable Slack notifications | No |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | No |
| `BRAND_NAME` | Report branding name | No |
| `COMPANY_NAME` | Your company name | No |
| `THEME` | Color theme: `linkedin`, `dark`, `corporate` | No |
| `REPORT_FOOTER` | Custom footer text on slides | No |
| `PDF_EXPORT` | Enable PDF export | No |
| `DATA_STORE_PATH` | SQLite database path | No |
| `WEBHOOK_API_KEY` | API key for webhook auth | No |
| `WEBHOOK_CALLBACK_URL` | External webhook callback URL | No |

</details>

---

## AI Insights Setup

### Ollama (Recommended - Free & Private)

```bash
# Install Ollama (https://ollama.com)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1

# That's it - the system auto-detects Ollama on port 11434
```

### Cloud AI (Optional)

```bash
# In your .env file:
ANTHROPIC_API_KEY=your_key    # Claude
OPENAI_API_KEY=your_key       # OpenAI
```

The system uses an automatic fallback chain: **Ollama -> Claude -> OpenAI -> rule-based analysis**. If Ollama is running locally, no API keys are needed.

---

## Google Sheets Integration

Demographics data is automatically uploaded to Google Sheets with formatted worksheets per campaign.

```bash
# 1. Create OAuth credentials at https://console.cloud.google.com
# 2. Download client_secret.json to config/
# 3. Run the auth script:
python scripts/google_auth.py
```

Sheets are auto-shared as "anyone with link can view" and linked from the PPTX report.

---

## Slide Types

Each report generates 40-60+ slides depending on the number of campaigns selected:

| Slide | Description |
|---|---|
| Title Slide | Report title, date range, branding |
| Executive Summary | KPI cards: impressions, clicks, CTR, engagements, cost |
| Campaign Overview | All campaigns in a comparison table |
| Impressions Chart | Bar chart comparing impressions across campaigns |
| Cost Analysis | CPC, CPM, budget utilization breakdown |
| Engagement Breakdown | Engagement rate analysis by campaign type |
| Monthly Trends | Time-series charts showing performance over time |
| Period Comparison | Period-over-period performance delta |
| Campaign Detail (per campaign) | Full metrics for each campaign |
| Creative Rankings (per campaign) | Top creatives with thumbnails and metrics |
| Demographics: Companies | Top companies reached |
| Demographics: Industries | Top industries reached |
| Demographics: Job Titles | Top job titles reached |
| Demographics: Job Functions | Top job functions reached |
| Demographics: Seniority | Seniority distribution |
| Demographics: Company Size | Company size distribution |
| Demographics: Geography | Geographic distribution |
| Demographics: Device | Mobile vs desktop breakdown |
| Aggregate Demographics | Cross-campaign industry, seniority, company size |
| Viral Performance | Viral impressions, clicks, likes, comments, shares |
| Lead Gen Funnel | Form opens, completions, cost per lead |
| Video Analytics | Views, completion rates, VTR metrics |
| A/B Test Results | Statistical comparison of creative variants |
| AI Insights | AI-generated analysis and recommendations |
| Budget Optimization | AI-recommended budget reallocation |
| 2026 Benchmarks | Performance benchmarks by format and industry |
| Closing Slide | Footer, branding, contact info |

---

## Project Structure

```
linkedin-report-automation/
├── app.py                        # Flask web dashboard (24 pages)
├── run.py                        # CLI entry point
├── src/
│   ├── config.py                 # Colors, fonts, themes, benchmarks
│   ├── linkedin_client.py        # LinkedIn Marketing API client (90+ metrics)
│   ├── report_generator.py       # PPTX report generator (40-60+ slides)
│   ├── ollama_insights.py        # AI insights (Ollama/Claude/OpenAI)
│   ├── data_store.py             # SQLite historical data storage
│   ├── formatters.py             # Number/date/currency formatting
│   ├── pptx_helpers.py           # Low-level PPTX helpers
│   ├── html_report.py            # Interactive HTML report generator
│   ├── sheets_uploader.py        # Google Sheets upload
│   ├── slides_exporter.py        # Google Slides export
│   ├── pdf_exporter.py           # PDF export via LibreOffice
│   ├── email_sender.py           # SMTP email delivery
│   ├── slack_notifier.py         # Slack webhook notifications
│   ├── ab_test_analyzer.py       # A/B test statistical analysis
│   ├── budget_optimizer.py       # Budget allocation optimization
│   ├── audience_recommender.py   # Demographic targeting recommendations
│   ├── token_refresh.py          # OAuth token management
│   ├── scheduled_report.py       # Automated report scheduling
│   ├── archiver.py               # Report archival & cleanup
│   ├── setup_wizard.py           # Guided configuration wizard
│   └── webhook_callbacks.py      # External webhook notifications
├── templates/                    # 24 Jinja2 HTML templates
│   ├── base.html                 # Master template with design system
│   ├── dashboard.html            # Main dashboard
│   ├── generate.html             # Report generation wizard
│   ├── campaign_detail.html      # Campaign deep-dive
│   ├── compare.html              # Side-by-side comparison
│   ├── demographics.html         # Demographic analysis
│   ├── trends.html               # Historical trends
│   ├── insights.html             # AI-powered insights
│   ├── creatives.html            # Creative gallery
│   ├── budget.html               # Budget & cost analysis
│   ├── roi.html                  # ROI calculator
│   ├── funnel.html               # Conversion funnel
│   ├── pacing.html               # Budget pacing
│   ├── whatif.html               # What-if simulator
│   ├── alerts.html               # Performance alerts
│   ├── schedules.html            # Report scheduling
│   ├── settings.html             # Configuration
│   └── ...                       # + 7 more pages
├── tests/                        # Unit test suite
├── scripts/
│   ├── google_auth.py            # Google OAuth setup
│   └── update_workflow.py        # n8n workflow updater
├── docs/
│   ├── API_REFERENCE.md          # API documentation
│   ├── DEPLOYMENT.md             # Deployment guide
│   └── FEATURES.md               # Feature matrix (85+ features)
├── assets/logo.png               # Company logo for reports
├── workflow.json                 # n8n workflow definition
├── start-n8n.sh                  # n8n startup script
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Docker Compose config
├── Procfile                      # Cloud deployment
├── render.yaml                   # Render.com one-click deploy
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .github/workflows/ci.yml      # CI/CD pipeline
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE                       # MIT
```

---

## LinkedIn API Reference

| Endpoint | Purpose |
|---|---|
| `GET /rest/adAccounts/{id}/adCampaigns` | Campaign details and metadata |
| `GET /v2/adAnalyticsV2` | Performance metrics (5 batches, 90+ fields) |
| `GET /rest/adAccounts/{id}/creatives/{urn}` | Creative details and associations |
| `GET /v2/shares/{id}` | Creative images and content |
| `GET /rest/organizationsLookup` | Company name resolution (batch) |
| `GET /v2/titles` | Job title resolution (batch) |
| `GET /v2/industries` | Industry resolution (batch) |
| `GET /v2/functions/{id}` | Job function resolution |
| `GET /v2/seniorities/{id}` | Seniority level resolution |
| `GET /v2/geo` | Geographic location resolution (batch) |

---

## Themes

Three built-in color themes. Set `THEME` in your `.env`:

- **`linkedin`** - Classic LinkedIn blue. Professional and familiar.
- **`dark`** - Deep navy with bright accents. Modern and bold.
- **`corporate`** - Charcoal and emerald. Clean and enterprise-ready.

---

## Running Tests

```bash
python -m unittest discover tests/
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, module structure, and code style guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Roadmap

- [x] LinkedIn Marketing API integration (90+ metrics, 5 batches)
- [x] Professional PPTX reports (40-60+ slides)
- [x] Interactive web dashboard (24 pages)
- [x] AI insights via Ollama / Claude / OpenAI
- [x] Google Sheets & Slides integration
- [x] Email & Slack delivery
- [x] A/B testing with statistical significance
- [x] Budget optimizer & audience recommender
- [x] ROI calculator & conversion funnel
- [x] What-if budget simulator
- [x] Scheduled report automation
- [x] Historical data & trend analysis
- [x] Docker support
- [x] CI/CD pipeline
- [ ] Hosted version (no setup required)
- [ ] White-label mode
- [ ] Custom AI model fine-tuning

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built by <strong><a href="https://www.linkedin.com/in/niketjain">Niket Jain</a></strong><br/>
  Python &bull; Flask &bull; LinkedIn Marketing API &bull; Chart.js &bull; Ollama
</p>
