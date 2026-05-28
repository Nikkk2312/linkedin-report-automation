# API Reference

## Modules

### `src/linkedin_client.py`

LinkedIn Marketing API client for fetching campaign data, analytics, demographics, and creatives.

#### Exception Classes

- **`LinkedInAPIError(message, status_code=None, response=None)`** - Base exception for LinkedIn API errors.
- **`LinkedInAuthError(message=..., response=None)`** - Raised on 401 Unauthorized responses.
- **`LinkedInRateLimitError(message=..., retry_after=None, response=None)`** - Raised on 429 Too Many Requests responses.

#### `LinkedInClient(access_token, account_id, rate_limit_delay=0.2, max_retries=2)`

Main API client class.

**Methods:**

| Method | Description |
|--------|-------------|
| `list_campaigns(status_filter=None)` | Fetch all campaigns from the ad account. Pass `'ACTIVE'` to filter. Returns list of campaign dicts. |
| `get_campaign_ids(campaigns_arg)` | Parse the `--campaigns` argument (`'all'`, `'active'`, or comma-separated IDs). Returns list of ID strings. |
| `get_campaign_detail(campaign_id)` | Fetch details for a single campaign. Returns campaign dict or None. |
| `fetch_analytics_batch1(campaign_id, date_range)` | Fetch primary analytics fields (impressions, clicks, cost, etc.). |
| `fetch_analytics_batch2(campaign_id, date_range)` | Fetch video analytics fields (videoViews, completions, etc.). |
| `fetch_analytics_batch3(campaign_id, date_range)` | Fetch viral metrics (viral impressions, clicks, likes, comments, shares, follows). |
| `fetch_analytics_batch4(campaign_id, date_range)` | Fetch lead gen metrics (form opens, completions, cost per lead). |
| `fetch_analytics_batch5(campaign_id, date_range)` | Fetch messaging, document, and device metrics. |
| `fetch_creative_analytics(campaign_id, date_range)` | Fetch per-creative analytics for a campaign. |
| `fetch_monthly_trends(campaign_id, date_range)` | Fetch monthly aggregated analytics. |
| `fetch_demographics(campaign_id, date_range, pivot)` | Fetch demographic breakdown by pivot (e.g., `MEMBER_COMPANY`). |
| `get_creative(creative_urn)` | Fetch creative detail by URN. |
| `get_creative_image_url(creative_data)` | Resolve image URL from creative data via share lookup. |
| `batch_resolve_orgs(org_ids)` | Resolve organization IDs to names in batches of 20. |
| `batch_resolve_titles(title_ids)` | Resolve job title IDs to names. |
| `batch_resolve_industries(industry_ids)` | Resolve industry IDs using static map + API fallback. |
| `batch_resolve_geo(geo_ids)` | Resolve geographic IDs to names. |
| `resolve_function(func_id)` | Resolve a single job function ID. |
| `resolve_seniority(sen_id)` | Resolve a single seniority ID. |
| `fetch_all_campaign_data(campaign_ids, progress_callback=None)` | Full data fetch for all campaigns. Returns dict with `'campaigns'` and `'report_date'` keys. |

**Usage Example:**

```python
from src.linkedin_client import LinkedInClient

client = LinkedInClient(access_token='YOUR_TOKEN', account_id='12345')
campaign_ids = client.get_campaign_ids('active')
data = client.fetch_all_campaign_data(campaign_ids)
```

---

### `src/report_generator.py`

Generates professional PPTX reports from campaign data JSON.

#### `generate_report(input_json_path, output_pptx_path, logo_path='assets/logo.png', csv_dir=None)`

Generate the full PPTX report from JSON input.

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_json_path` | `str` | Path to the input JSON file (output from `fetch_all_campaign_data`). |
| `output_pptx_path` | `str` | Path where the PPTX file will be saved. |
| `logo_path` | `str` | Path to logo image file (optional). |
| `csv_dir` | `str` | Directory for CSV demographic exports (optional). |

**Usage Example:**

```python
from src.report_generator import generate_report

generate_report('output/data.json', 'output/report.pptx', logo_path='assets/logo.png')
```

---

### `src/formatters.py`

Number and date formatting utilities used across the codebase.

| Function | Signature | Description |
|----------|-----------|-------------|
| `format_number` | `(n) -> str` | Format number with commas. Returns `'NA'` for None. |
| `format_ctr` | `(impressions, clicks) -> str` | Calculate and format CTR as percentage string. |
| `calc_ctr_value` | `(impressions, clicks) -> float or None` | Calculate CTR as a float value. |
| `format_date_ordinal` | `(date_str) -> str` | Convert `'YYYY-MM-DD'` to `'8th Dec 2025'` format. |
| `format_percentage` | `(value, decimals=1) -> str` | Format a float as percentage string. |
| `format_currency` | `(amount, currency='USD') -> str` | Format amount as currency with symbol. |
| `abbreviate_number` | `(n) -> str` | Abbreviate large numbers (e.g., `1.2M`, `45.0K`). |

---

### `src/config.py`

Configuration constants for colors, fonts, slide dimensions, and themes.

#### `get_theme(name=None) -> dict`

Return a theme dict by name. Falls back to the `'linkedin'` theme if name is unknown.
Available themes: `'linkedin'`, `'dark'`, `'corporate'`.

Theme keys: `primary`, `accent`, `success`, `danger`, `bg`, `text` (each a 3-tuple of RGB ints).

**Environment Variables:**
- `THEME` - Default theme name (default: `'linkedin'`)
- `BRAND_NAME` - Brand name for reports
- `BRAND_TAGLINE` - Brand tagline
- `COMPANY_NAME` - Company name
- `REPORT_FOOTER` - Custom footer text
- `SLIDE_FOOTER_ENABLED` - Enable/disable footer (`'true'`/`'false'`)

---

### `src/pdf_exporter.py`

PDF export using LibreOffice CLI.

#### `export_pdf(pptx_path, pdf_path=None) -> str`

Convert a PPTX file to PDF. Returns the PDF file path on success, or empty string on failure.

---

### `src/pptx_helpers.py`

Low-level PPTX helper functions for cell formatting, shapes, and layout.

| Function | Description |
|----------|-------------|
| `set_cell_border(cell, color, width)` | Set borders on a table cell. |
| `set_cell_fill(cell, color)` | Set solid fill on a table cell. |
| `set_cell_text(cell, text, ...)` | Set formatted text in a table cell. |
| `add_logo(slide, logo_path)` | Add logo to top-right corner. |
| `add_slide_bg(slide)` | Set white background. |
| `add_accent_bar(slide, top)` | Add thin accent bar at bottom. |
| `add_top_line(slide)` | Add separator line below header. |
| `add_top_band(slide)` | Add blue accent band at top. |
| `add_orange_accent(slide, left, top, width)` | Add thin orange accent line. |
| `add_heading(slide, text, ...)` | Add a heading textbox. |
| `add_hyperlink(slide, run, url)` | Add a hyperlink to a text run. |

---

### `src/sheets_uploader.py`

Upload demographics CSV files to Google Sheets.

#### `upload_to_sheets(csv_dir, report_date) -> str`

Create a Google Sheet with demographics data. Returns the sheet URL or empty string on failure.

---

### `src/ollama_insights.py`

AI-powered insights generation with multi-provider fallback chain.

#### `check_ollama_available() -> tuple[bool, list[str]]`

Check if Ollama is running locally. Returns a tuple of (is_available, list_of_model_names).

#### `generate_insights(campaigns) -> list[str]`

Generate AI insights for the given campaign data. Uses fallback chain: Ollama -> Claude -> OpenAI -> rule-based.

| Parameter | Type | Description |
|-----------|------|-------------|
| `campaigns` | `list[dict]` | List of campaign data dicts with metrics (impressions, clicks, cost, etc.). |

Returns a list of insight strings, or empty list if all providers fail.

#### `generate_executive_summary(campaigns) -> str`

Generate an AI-powered executive summary of all campaigns. Uses the same fallback chain as `generate_insights`.

#### Internal Functions

| Function | Description |
|----------|-------------|
| `_build_campaign_summary(campaigns)` | Build a text summary of campaign metrics for use as AI prompt context. |
| `_try_ollama(prompt)` | Attempt to generate insights using local Ollama instance. Returns response or None. |
| `_try_anthropic(prompt)` | Attempt to generate insights using Claude API. Returns response or None. |
| `_try_openai(prompt)` | Attempt to generate insights using OpenAI API. Returns response or None. |

**Usage Example:**

```python
from src.ollama_insights import generate_insights, check_ollama_available

# Check if Ollama is available
ok, models = check_ollama_available()
print(f"Ollama available: {ok}, models: {models}")

# Generate insights
campaigns = [{'name': 'Campaign 1', 'impressions': 50000, 'clicks': 1200, 'cost_usd': 500}]
insights = generate_insights(campaigns)
for insight in insights:
    print(insight)
```

---

### `src/setup_wizard.py`

Interactive setup wizard for guided project configuration.

Run via: `python -m src.setup_wizard`

The wizard walks users through:
- LinkedIn API credential configuration
- Ollama AI setup and model selection
- Google Sheets integration setup
- Email and Slack notification configuration
- Theme and branding selection
- Writing the `.env` file

**Usage:**

```bash
python -m src.setup_wizard
```

---

### New LinkedIn API Fields (v1.2)

The LinkedIn API client now fetches 90+ metrics across 5 API batches. Key new fields include:

| Field | Batch | Description |
|-------|-------|-------------|
| `viralImpressions` | 3 | Impressions from viral/shared activity |
| `viralClicks` | 3 | Clicks from viral/shared activity |
| `viralLikes` | 3 | Likes from viral/shared activity |
| `viralComments` | 3 | Comments from viral/shared activity |
| `viralShares` | 3 | Shares from viral/shared activity |
| `viralFollows` | 3 | Follows from viral/shared activity |
| `leadGenerationMailContactInfoShares` | 4 | Lead form completions |
| `leadGenerationMailInterestedClicks` | 4 | Lead form opens |
| `costPerLead` | 4 (derived) | Cost per lead gen form completion |
| `messagingSends` | 5 | Message sends for messaging ads |
| `messagingOpens` | 5 | Message opens for messaging ads |
| `documentCompletions` | 5 | Document ad completions |
| `documentFirstQuartileCompletions` | 5 | Document 25% completion |
| `deviceType` | 5 | Device breakdown (mobile vs desktop) |
| `servingLocation` | 5 | Serving location (onsite vs offsite) |

---

### `run.py`

CLI entry point. See `python run.py --help` for all options.

```
python run.py --token YOUR_TOKEN --account-id 12345 --campaigns 123,456,789
python run.py --env .env --campaigns all
python run.py --env .env --campaigns active --output output/my_report.pptx --pdf
```
