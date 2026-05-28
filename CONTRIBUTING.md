# Contributing

## Dev Environment Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your LinkedIn API credentials.

4. (Optional) Install LibreOffice for PDF export support.

5. (Optional) Set up Ollama for local AI insights:
   ```bash
   # Install Ollama from https://ollama.com
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull a model (llama3.1 recommended for development)
   ollama pull llama3.1

   # Verify Ollama is running
   curl http://localhost:11434/api/tags
   ```

6. (Optional) Set up Google OAuth for Sheets integration:
   ```bash
   python scripts/google_auth.py
   ```

7. (Optional) Run the setup wizard for guided configuration:
   ```bash
   python -m src.setup_wizard
   ```

## Running Reports

### Via n8n (web UI)
```bash
bash start-n8n.sh
# Open http://localhost:5678
```

### Via CLI (standalone)
```bash
python run.py --env .env --campaigns active
python run.py --env .env --campaigns 123,456,789 --pdf
python run.py --env .env --campaigns all --json-only
```

### Via Docker
```bash
docker compose up --build
```

## Running Tests

### Unit tests
```bash
python -m unittest discover tests/
```

### Syntax check
```bash
python -m py_compile run.py
python -m py_compile src/report_generator.py
python -m py_compile src/linkedin_client.py
```

### Import test
```bash
python -c "from src.linkedin_client import LinkedInClient; print('OK')"
python -c "from src.report_generator import generate_report; print('OK')"
python -c "from src.config import ANTHROPIC_MODEL, EMAIL_ENABLED, SLACK_ENABLED; print('OK')"
python -c "from src.ollama_insights import generate_insights, check_ollama_available; print('OK')"
python -c "from src.setup_wizard import main; print('OK')"
```

### Generate from existing JSON
```bash
python -m src.report_generator output/test_data.json output/test_output.pptx
```

## Module Structure

The project is organized into the following modules under `src/`:

| Module | Purpose |
|---|---|
| `config.py` | Colors, fonts, themes, branding, and feature flag constants |
| `formatters.py` | Number, date, currency, and percentage formatting utilities |
| `linkedin_client.py` | LinkedIn Marketing API client with rate limiting and retries |
| `pdf_exporter.py` | PDF export via LibreOffice subprocess |
| `pptx_helpers.py` | Low-level PPTX cell, shape, and layout helpers |
| `report_generator.py` | Main report generator — all 40-60+ slide types |
| `ollama_insights.py` | AI insights via Ollama/Claude/OpenAI with fallback chain |
| `setup_wizard.py` | Guided interactive setup wizard |
| `sheets_uploader.py` | Google Sheets demographic data upload |

## Adding New Slide Types

1. Add a new function in `src/report_generator.py` following the pattern:
   ```python
   def create_my_new_slide(prs, data, logo_path):
       slide = prs.slides.add_slide(prs.slide_layouts[6])
       add_slide_bg(slide)
       add_heading(slide, 'My New Slide')
       add_top_line(slide)
       # ... add shapes, tables, charts ...
       add_logo(slide, logo_path)
   ```

2. Call it from `generate_report()` in the appropriate position.

3. Use helpers from `src/pptx_helpers.py` for consistent styling:
   - `set_cell_text()`, `set_cell_fill()`, `set_cell_border()` for tables
   - `add_heading()`, `add_top_band()`, `add_orange_accent()` for layout
   - `add_logo()` at the end of every slide

4. Use formatters from `src/formatters.py` for number display:
   - `format_number()`, `format_currency()`, `format_percentage()`
   - `abbreviate_number()` for large values in charts

5. Colors and fonts are defined in `src/config.py`.

## Adding New Demographic Slides

Demographics slides follow a consistent pattern (8 per campaign). To add a new demographic dimension:

1. Add the new LinkedIn API pivot to `linkedin_client.py` (e.g., `MEMBER_NEW_DIMENSION`).

2. Add a resolution function if needed (e.g., `batch_resolve_new_dimension()`).

3. Create the slide function in `report_generator.py` following the demographics pattern:
   ```python
   def create_demographics_new_dimension_slide(prs, campaign, demo_data, logo_path):
       slide = prs.slides.add_slide(prs.slide_layouts[6])
       add_slide_bg(slide)
       add_heading(slide, f"{campaign['name']} - New Dimension")
       # ... add table or chart with demo_data ...
       add_logo(slide, logo_path)
   ```

4. Call it from the demographics section in `generate_report()`.

5. Add the corresponding aggregate slide for cross-campaign analysis.

6. Update the slide count in README.md and docs/FEATURES.md.

## Adding New Automation Modules

To add a new automation module (e.g., a new delivery channel or data source):

1. Create a new file in `src/` (e.g., `src/my_module.py`).

2. Add any new dependencies to `requirements.txt`.

3. Add configuration constants to `src/config.py` following the existing pattern:
   ```python
   MY_FEATURE_ENABLED = os.getenv('MY_FEATURE', 'false').lower() == 'true'
   ```

4. Add the corresponding environment variables to `.env.example` with documentation.

5. Wire the module into `report_generator.py` or `run.py` as appropriate.

6. Add import checks to `.github/workflows/ci.yml`:
   ```yaml
   - name: Import test - my_module
     run: python -c "from src.my_module import MyClass; print('my_module OK')"
   ```

7. Write unit tests in `tests/test_my_module.py`.

8. Update `docs/FEATURES.md` with the new feature details.

## Code Style

- Python 3.11+
- No docstrings required for private functions (prefixed with `_`)
- Public functions should have a brief docstring
- Use type hints where it improves clarity
- Constants in `UPPER_SNAKE_CASE`, functions in `lower_snake_case`
- Imports: stdlib, then third-party, then local (separated by blank lines)
