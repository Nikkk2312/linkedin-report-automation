"""
Setup wizard for LinkedIn Report Automation.
Run: python -m src.setup_wizard
Serves a web form at http://localhost:8899 for initial configuration.
"""

import http.server
import json
import os
import sys
import urllib.parse
import webbrowser
from pathlib import Path

PORT = 8899
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

def _load_env():
    """Load current .env values."""
    values = {}
    if os.path.isfile(ENV_PATH):
        with open(ENV_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    values[key.strip()] = val.strip()
    return values

def _save_env(values):
    """Save values to .env file."""
    lines = []
    lines.append("# LinkedIn API Credentials")
    lines.append(f"LINKEDIN_ACCESS_TOKEN={values.get('LINKEDIN_ACCESS_TOKEN', '')}")
    lines.append(f"LINKEDIN_ACCOUNT_ID={values.get('LINKEDIN_ACCOUNT_ID', '')}")
    lines.append(f"LINKEDIN_CLIENT_ID={values.get('LINKEDIN_CLIENT_ID', '')}")
    lines.append(f"LINKEDIN_CLIENT_SECRET={values.get('LINKEDIN_CLIENT_SECRET', '')}")
    lines.append(f"LINKEDIN_REFRESH_TOKEN={values.get('LINKEDIN_REFRESH_TOKEN', '')}")
    lines.append("")
    lines.append("# n8n Configuration")
    lines.append(f"N8N_ENCRYPTION_KEY={values.get('N8N_ENCRYPTION_KEY', '')}")
    lines.append(f"N8N_PORT={values.get('N8N_PORT', '5678')}")
    lines.append(f"N8N_OWNER_EMAIL={values.get('N8N_OWNER_EMAIL', '')}")
    lines.append(f"N8N_OWNER_PASSWORD={values.get('N8N_OWNER_PASSWORD', '')}")
    lines.append("")
    lines.append("# AI Insights (Ollama - free, local)")
    lines.append(f"OLLAMA_ENABLED={values.get('OLLAMA_ENABLED', 'true')}")
    lines.append(f"OLLAMA_MODEL={values.get('OLLAMA_MODEL', 'llama3.1')}")
    lines.append(f"OLLAMA_BASE_URL={values.get('OLLAMA_BASE_URL', 'http://localhost:11434')}")
    lines.append(f"ANTHROPIC_API_KEY={values.get('ANTHROPIC_API_KEY', '')}")
    lines.append(f"OPENAI_API_KEY={values.get('OPENAI_API_KEY', '')}")
    lines.append("")
    lines.append("# Email Delivery")
    lines.append(f"EMAIL_SMTP_HOST={values.get('EMAIL_SMTP_HOST', 'smtp.gmail.com')}")
    lines.append(f"EMAIL_SMTP_PORT={values.get('EMAIL_SMTP_PORT', '587')}")
    lines.append(f"EMAIL_SENDER={values.get('EMAIL_SENDER', '')}")
    lines.append(f"EMAIL_PASSWORD={values.get('EMAIL_PASSWORD', '')}")
    lines.append("")
    lines.append("# Slack")
    lines.append(f"SLACK_WEBHOOK_URL={values.get('SLACK_WEBHOOK_URL', '')}")
    lines.append("")
    lines.append("# Branding")
    lines.append(f"BRAND_NAME={values.get('BRAND_NAME', 'LinkedIn Report Automation')}")
    lines.append(f"COMPANY_NAME={values.get('COMPANY_NAME', '')}")
    lines.append(f"THEME={values.get('THEME', 'linkedin')}")
    lines.append("")
    lines.append("# Webhook Security")
    lines.append(f"WEBHOOK_API_KEY={values.get('WEBHOOK_API_KEY', '')}")

    with open(ENV_PATH, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def _test_linkedin(token, account_id):
    """Test LinkedIn API connection."""
    import requests
    try:
        resp = requests.get(
            f'https://api.linkedin.com/rest/adAccounts/{account_id}/adCampaigns?q=search&count=1',
            headers={
                'Authorization': f'Bearer {token}',
                'LinkedIn-Version': '202503',
                'X-Restli-Protocol-Version': '2.0.0'
            },
            timeout=10
        )
        if resp.status_code == 200:
            total = len(resp.json().get('elements', []))
            return True, f"Connected! Found campaigns in account {account_id}"
        elif resp.status_code == 401:
            return False, "Invalid or expired access token"
        else:
            return False, f"API error: {resp.status_code}"
    except Exception as e:
        return False, str(e)

def _test_ollama():
    """Test Ollama connection."""
    import requests
    try:
        resp = requests.get('http://localhost:11434/api/tags', timeout=5)
        if resp.status_code == 200:
            models = [m.get('name', '') for m in resp.json().get('models', [])]
            return True, f"Connected! Models: {', '.join(models[:5])}"
    except:
        pass
    return False, "Ollama not running. Install from https://ollama.ai and run: ollama pull llama3.1"


# Build a complete HTML page for the setup wizard with:
# Step 1: LinkedIn API (token, account ID, client ID) with Test Connection button
# Step 2: AI Setup (Ollama vs Claude vs OpenAI) with Test button
# Step 3: Email delivery (optional)
# Step 4: Branding (name, theme dropdown)
# Step 5: Review & Save
# Use a clean, modern design with step indicators
# Form POSTs to /save, /test-linkedin, /test-ollama endpoints

WIZARD_HTML = """<!DOCTYPE html>
<html>
<head>
<title>LinkedIn Report Automation - Setup</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1e293b; }
  .container { max-width: 700px; margin: 40px auto; padding: 0 20px; }
  .header { background: linear-gradient(135deg, #0A66C2, #004B87); color: white; padding: 32px; border-radius: 12px 12px 0 0; text-align: center; }
  .header h1 { font-size: 24px; margin-bottom: 8px; }
  .header p { opacity: 0.85; font-size: 14px; }
  .steps { display: flex; justify-content: center; gap: 8px; margin: 20px 0 0; }
  .step-dot { width: 12px; height: 12px; border-radius: 50%; background: rgba(255,255,255,0.3); }
  .step-dot.active { background: white; }
  .step-dot.done { background: #22c55e; }
  .card { background: white; border-radius: 0 0 12px 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px; }
  .section { margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 24px; }
  .section:last-child { border-bottom: none; }
  .section h2 { font-size: 18px; color: #0A66C2; margin-bottom: 4px; }
  .section p.desc { font-size: 13px; color: #64748b; margin-bottom: 16px; }
  label { display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 4px; }
  input, select { width: 100%; padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; margin-bottom: 12px; }
  input:focus, select:focus { outline: none; border-color: #0A66C2; box-shadow: 0 0 0 3px rgba(10,102,194,0.15); }
  .row { display: flex; gap: 12px; }
  .row > div { flex: 1; }
  .btn { padding: 10px 24px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
  .btn-primary { background: #0A66C2; color: white; }
  .btn-primary:hover { background: #004B87; }
  .btn-secondary { background: #e2e8f0; color: #334155; }
  .btn-secondary:hover { background: #cbd5e1; }
  .btn-test { background: #f0fdf4; color: #166534; border: 1px solid #86efac; font-size: 13px; padding: 8px 16px; }
  .btn-test:hover { background: #dcfce7; }
  .status { font-size: 13px; padding: 8px 12px; border-radius: 6px; margin-top: 8px; display: none; }
  .status.ok { display: block; background: #f0fdf4; color: #166534; border: 1px solid #86efac; }
  .status.err { display: block; background: #fef2f2; color: #991b1b; border: 1px solid #fca5a5; }
  .actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
  .optional { font-size: 11px; color: #94a3b8; font-weight: normal; }
  .footer { text-align: center; padding: 20px; color: #94a3b8; font-size: 12px; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>LinkedIn Report Automation</h1>
    <p>Initial Setup - Configure your connections</p>
    <div class="steps">
      <div class="step-dot active"></div>
      <div class="step-dot"></div>
      <div class="step-dot"></div>
      <div class="step-dot"></div>
    </div>
  </div>
  <div class="card">
    <form id="setupForm" method="POST" action="/save">

      <div class="section">
        <h2>Step 1: LinkedIn API</h2>
        <p class="desc">Enter your LinkedIn Marketing API credentials. <a href="https://www.linkedin.com/developers/apps" target="_blank">Get them here</a></p>
        <label>Access Token <span style="color:red">*</span></label>
        <input type="text" name="LINKEDIN_ACCESS_TOKEN" value="{LINKEDIN_ACCESS_TOKEN}" required placeholder="AQX...">
        <label>Ad Account ID <span style="color:red">*</span></label>
        <input type="text" name="LINKEDIN_ACCOUNT_ID" value="{LINKEDIN_ACCOUNT_ID}" required placeholder="123456789">
        <div class="row">
          <div><label>Client ID <span class="optional">(optional)</span></label><input type="text" name="LINKEDIN_CLIENT_ID" value="{LINKEDIN_CLIENT_ID}" placeholder="86xxx"></div>
          <div><label>Client Secret <span class="optional">(for token refresh)</span></label><input type="text" name="LINKEDIN_CLIENT_SECRET" value="{LINKEDIN_CLIENT_SECRET}" placeholder=""></div>
        </div>
        <button type="button" class="btn btn-test" onclick="testLinkedIn()">Test Connection</button>
        <div id="linkedinStatus" class="status"></div>
      </div>

      <div class="section">
        <h2>Step 2: AI Insights <span class="optional">(recommended)</span></h2>
        <p class="desc">Free AI insights via <a href="https://ollama.ai" target="_blank">Ollama</a> (local), or use Claude/OpenAI API</p>
        <label>AI Provider</label>
        <select name="AI_PROVIDER" onchange="toggleAI(this.value)">
          <option value="ollama">Ollama (Free, Local, Private)</option>
          <option value="anthropic">Claude API (Paid, Best Quality)</option>
          <option value="openai">OpenAI API (Paid)</option>
          <option value="none">Disable AI Insights</option>
        </select>
        <div id="ollamaFields">
          <label>Ollama Model</label>
          <input type="text" name="OLLAMA_MODEL" value="{OLLAMA_MODEL}" placeholder="llama3.1">
          <button type="button" class="btn btn-test" onclick="testOllama()">Test Ollama</button>
          <div id="ollamaStatus" class="status"></div>
        </div>
        <div id="anthropicFields" style="display:none">
          <label>Anthropic API Key</label>
          <input type="text" name="ANTHROPIC_API_KEY" value="{ANTHROPIC_API_KEY}" placeholder="sk-ant-...">
        </div>
        <div id="openaiFields" style="display:none">
          <label>OpenAI API Key</label>
          <input type="text" name="OPENAI_API_KEY" value="{OPENAI_API_KEY}" placeholder="sk-...">
        </div>
      </div>

      <div class="section">
        <h2>Step 3: Email Delivery <span class="optional">(optional)</span></h2>
        <p class="desc">Send reports via email when generated</p>
        <div class="row">
          <div><label>SMTP Host</label><input type="text" name="EMAIL_SMTP_HOST" value="{EMAIL_SMTP_HOST}" placeholder="smtp.gmail.com"></div>
          <div><label>SMTP Port</label><input type="text" name="EMAIL_SMTP_PORT" value="{EMAIL_SMTP_PORT}" placeholder="587"></div>
        </div>
        <div class="row">
          <div><label>Sender Email</label><input type="email" name="EMAIL_SENDER" value="{EMAIL_SENDER}" placeholder="you@gmail.com"></div>
          <div><label>App Password</label><input type="password" name="EMAIL_PASSWORD" value="{EMAIL_PASSWORD}" placeholder="xxxx xxxx xxxx xxxx"></div>
        </div>
      </div>

      <div class="section">
        <h2>Step 4: Branding <span class="optional">(optional)</span></h2>
        <p class="desc">Customize the look of your reports</p>
        <div class="row">
          <div><label>Brand Name</label><input type="text" name="BRAND_NAME" value="{BRAND_NAME}" placeholder="Your Company"></div>
          <div><label>Company Name</label><input type="text" name="COMPANY_NAME" value="{COMPANY_NAME}" placeholder=""></div>
        </div>
        <label>Color Theme</label>
        <select name="THEME">
          <option value="linkedin" {theme_linkedin}>LinkedIn Blue</option>
          <option value="dark" {theme_dark}>Dark Mode</option>
          <option value="corporate" {theme_corporate}>Corporate</option>
        </select>
        <label>Webhook API Key <span class="optional">(for security)</span></label>
        <input type="text" name="WEBHOOK_API_KEY" value="{WEBHOOK_API_KEY}" placeholder="Leave empty for no auth">
      </div>

      <div class="actions">
        <button type="submit" class="btn btn-primary">Save Configuration</button>
      </div>
    </form>
  </div>
  <div class="footer">LinkedIn Report Automation v1.1.0</div>
</div>

<script>
function toggleAI(val) {
  document.getElementById('ollamaFields').style.display = val === 'ollama' ? 'block' : 'none';
  document.getElementById('anthropicFields').style.display = val === 'anthropic' ? 'block' : 'none';
  document.getElementById('openaiFields').style.display = val === 'openai' ? 'block' : 'none';
}
async function testLinkedIn() {
  const s = document.getElementById('linkedinStatus');
  s.className = 'status'; s.textContent = 'Testing...'; s.style.display = 'block';
  const token = document.querySelector('[name=LINKEDIN_ACCESS_TOKEN]').value;
  const acct = document.querySelector('[name=LINKEDIN_ACCOUNT_ID]').value;
  try {
    const r = await fetch('/test-linkedin?token=' + encodeURIComponent(token) + '&account=' + acct);
    const d = await r.json();
    s.className = 'status ' + (d.ok ? 'ok' : 'err');
    s.textContent = d.message;
  } catch(e) { s.className = 'status err'; s.textContent = 'Test failed: ' + e; }
}
async function testOllama() {
  const s = document.getElementById('ollamaStatus');
  s.className = 'status'; s.textContent = 'Testing...'; s.style.display = 'block';
  try {
    const r = await fetch('/test-ollama');
    const d = await r.json();
    s.className = 'status ' + (d.ok ? 'ok' : 'err');
    s.textContent = d.message;
  } catch(e) { s.className = 'status err'; s.textContent = 'Test failed: ' + e; }
}
</script>
</body>
</html>"""

# Build the SUCCESS page HTML (shown after saving)
SUCCESS_HTML = """<!DOCTYPE html>
<html><head><title>Setup Complete</title>
<style>body{font-family:'Segoe UI',sans-serif;background:#f0f4f8;display:flex;justify-content:center;align-items:center;min-height:100vh}
.card{background:white;border-radius:12px;padding:48px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:500px}
.check{font-size:64px;margin-bottom:16px}h1{color:#166534;margin-bottom:8px}p{color:#64748b;margin-bottom:24px}
a{color:#0A66C2;text-decoration:none;font-weight:600}a:hover{text-decoration:underline}
</style></head><body><div class="card">
<div class="check">&#10004;</div>
<h1>Setup Complete!</h1>
<p>Your configuration has been saved to .env</p>
<p><a href="http://localhost:{n8n_port}/webhook/linkedin-report-v2">Open Report Generator</a></p>
<p style="font-size:13px;color:#94a3b8">You can re-run this wizard anytime:<br><code>python -m src.setup_wizard</code></p>
</div></body></html>"""


class SetupHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            env = _load_env()
            html = WIZARD_HTML
            # Replace placeholders
            for key in ['LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_ACCOUNT_ID', 'LINKEDIN_CLIENT_ID',
                        'LINKEDIN_CLIENT_SECRET', 'OLLAMA_MODEL', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY',
                        'EMAIL_SMTP_HOST', 'EMAIL_SMTP_PORT', 'EMAIL_SENDER', 'EMAIL_PASSWORD',
                        'BRAND_NAME', 'COMPANY_NAME', 'WEBHOOK_API_KEY']:
                html = html.replace('{' + key + '}', env.get(key, ''))
            theme = env.get('THEME', 'linkedin')
            html = html.replace('{theme_linkedin}', 'selected' if theme == 'linkedin' else '')
            html = html.replace('{theme_dark}', 'selected' if theme == 'dark' else '')
            html = html.replace('{theme_corporate}', 'selected' if theme == 'corporate' else '')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())

        elif self.path.startswith('/test-linkedin'):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            token = params.get('token', [''])[0]
            account = params.get('account', [''])[0]
            ok, msg = _test_linkedin(token, account)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': ok, 'message': msg}).encode())

        elif self.path == '/test-ollama':
            ok, msg = _test_ollama()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': ok, 'message': msg}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/save':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(body)

            env = _load_env()
            for key, vals in params.items():
                env[key] = vals[0]

            # Handle AI provider selection
            ai_provider = params.get('AI_PROVIDER', ['ollama'])[0]
            if ai_provider == 'none':
                env['AI_INSIGHTS_ENABLED'] = 'false'
                env['OLLAMA_ENABLED'] = 'false'
            elif ai_provider == 'ollama':
                env['AI_INSIGHTS_ENABLED'] = 'true'
                env['OLLAMA_ENABLED'] = 'true'
            else:
                env['AI_INSIGHTS_ENABLED'] = 'true'
                env['OLLAMA_ENABLED'] = 'false'

            _save_env(env)

            n8n_port = env.get('N8N_PORT', '5678')
            html = SUCCESS_HTML.replace('{n8n_port}', n8n_port)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"  [Setup] {args[0]}", file=sys.stderr)


def main():
    print(f"Starting setup wizard at http://localhost:{PORT}", file=sys.stderr)
    print(f"Opening browser...", file=sys.stderr)
    server = http.server.HTTPServer(('', PORT), SetupHandler)
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass
    print(f"Setup wizard running at http://localhost:{PORT}", file=sys.stderr)
    print(f"Press Ctrl+C to stop", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSetup wizard stopped.", file=sys.stderr)


if __name__ == '__main__':
    main()
