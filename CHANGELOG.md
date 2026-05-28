# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-05-28

### Added - Web Dashboard
- Full-stack Flask web dashboard with 24 interactive pages
- Dashboard home with KPI cards, sparklines, top performers, and recent reports
- Multi-step report generation wizard with API connection testing
- Campaign detail page with health scoring, radar charts, and engagement breakdown
- Side-by-side report comparison (up to 5 reports)
- Demographics analysis with 11 pivots and CSV export
- Historical trends with multi-metric analysis and period-over-period comparison
- AI insights page with strategic analysis, budget optimization, and audience targeting
- Creative gallery with sortable performance metrics
- Budget and cost analysis with efficiency scoring
- ROI/ROAS calculator with per-campaign breakdown
- Conversion funnel visualization
- Budget pacing analyzer with gauge charts and projections
- What-if budget simulator with interactive sliders
- Performance alert configuration with email/Slack notifications
- Scheduled report automation (daily/weekly/biweekly/monthly)
- Report templates for quick generation
- Report viewer with toggleable sections, comments, and version history
- Shareable read-only report links
- Activity log timeline
- Settings page with account profiles and import/export
- Interactive API documentation page
- Searchable glossary of metrics, benchmarks, and features
- Dark mode support across all pages

### Added - Infrastructure
- Procfile for cloud deployment (Render, Railway, Fly.io)
- render.yaml for Render.com one-click deploy
- Updated Dockerfile with Flask dashboard support
- Updated docker-compose.yml with separate dashboard and n8n services

### Added - Backend Modules
- `app.py` - Flask web application with job tracking, comments, version history
- `src/data_store.py` - SQLite historical data storage with trend queries
- `src/html_report.py` - Self-contained HTML reports with Chart.js
- `src/ab_test_analyzer.py` - Statistical A/B test analysis with z-tests
- `src/budget_optimizer.py` - Budget reallocation optimization
- `src/audience_recommender.py` - Demographic targeting recommendations
- `src/archiver.py` - Report archival and cleanup
- `src/webhook_callbacks.py` - External webhook notifications

### Changed
- Version bumped to 2.0.0 (major release with web dashboard)
- Updated project structure documentation

---

## [1.2.0] - 2026-05-24

### Added
- Professional demographics slides in PPTX (8 slides per campaign)
  - Top Companies, Industries, Job Titles, Job Functions
  - Seniority Distribution, Company Size Distribution
  - Geographic Distribution, Device Breakdown
- Aggregate demographics slides across all campaigns
- All 90+ LinkedIn API metrics (5 API batches)
- Viral performance analysis slides
- Lead generation funnel slides
- Messaging ads performance slides
- Document ads performance slides
- AI insights via Ollama (free, local, private)
- Fallback chain: Ollama -> Claude -> OpenAI -> rule-based
- Setup wizard (python -m src.setup_wizard)
- 2026 industry benchmarks by format and industry
- Device type breakdown (mobile vs desktop)
- Serving location analytics (onsite vs offsite)
- 30+ derived metrics (viral amplification, frequency, video completion rate, etc.)

### Changed
- Slide count increased from 30+ to 40-60+ per report (depending on campaigns)
- AI insights now use Ollama as primary provider (free, local)
- LinkedIn API client fetches 90+ metrics across 5 batches

---

## [1.1.0] - 2026-05-24

### Added - AI & Analytics
- AI-powered campaign insights and recommendations via Claude API (Anthropic)
- AI-generated budget optimization suggestions
- AI-driven audience targeting recommendations
- Anomaly detection and alerting for campaign metrics
- Natural language summaries of key performance indicators

### Added - Report Enhancements
- 30+ slide types (up from 21)
- Cost analysis slides with CPC, CPM, and budget utilization
- Engagement rate analysis and benchmark slides
- Monthly trend charts with time-series data
- Period-over-period comparison slides
- Video analytics slides (views, completion rates, view-through rate)
- A/B testing analysis with statistical significance
- Creative variant comparison slides
- Budget optimization recommendation slides
- HTML report generation alongside PPTX

### Added - Delivery & Notifications
- Email delivery via SMTP with formatted HTML summaries
- Slack notifications with KPI highlights and report links
- Webhook callbacks for external system integration
- Webhook API authentication via API key

### Added - Data & Storage
- SQLite-based historical data storage
- Configurable data retention and archiving (REPORT_ARCHIVE_DAYS)
- Trend analysis with historical baselines
- Period-over-period comparison using stored data

### Added - Infrastructure
- Docker support with persistent data volumes
- Unit test suite (tests/)
- CI pipeline runs unit tests
- VERSION file for release tracking

---

## [1.0.0] - 2026-05-24

### Added
- LinkedIn Marketing API integration for ad campaign data retrieval
- Professional PPTX report generation with 21+ slides per report
- Executive Summary slide with KPI cards
- Campaign Overview table with color-coded CTR benchmarking
- Impressions Comparison bar chart across campaigns
- Per-campaign detail slides with full performance metrics
- Creative performance rankings with image thumbnails
- Full demographic name resolution via LinkedIn API
- LinkedIn Industry Taxonomy v2 support (434 industries)
- Google Sheets integration for demographic data upload
- n8n workflow automation with webhook-triggered report generation
- Configurable color themes (linkedin, dark, corporate)
- Custom branding support
- CLI mode for direct report generation
- MIT License
