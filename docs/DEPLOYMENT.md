# Deployment Guide

## Table of Contents

- [Manual Deployment](#manual-deployment)
- [Docker Deployment](#docker-deployment)
- [HTTPS Setup with Nginx](#https-setup-with-nginx)
- [Environment Variables Reference](#environment-variables-reference)

---

## Manual Deployment

### Prerequisites

- Python 3.9+
- pip
- LibreOffice (optional, for PDF export)

### Steps

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd linkedin-report-automation
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   Create a `.env` file in the project root:

   ```env
   LINKEDIN_ACCESS_TOKEN=your_token_here
   LINKEDIN_ACCOUNT_ID=your_account_id
   BRAND_NAME=Your Company
   THEME=linkedin
   ```

5. **Run the report generator:**

   ```bash
   python run.py --env .env --campaigns active
   ```

6. **Output** is saved to the `output/` directory by default.

### Install LibreOffice (for PDF export)

- **Ubuntu/Debian:** `sudo apt install libreoffice`
- **macOS:** `brew install --cask libreoffice`
- **Windows:** Download from [libreoffice.org](https://www.libreoffice.org/)

---

## Docker Deployment

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Install LibreOffice for PDF export
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice-impress && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p output

ENTRYPOINT ["python", "run.py"]
```

### Build and Run

```bash
# Build
docker build -t linkedin-report .

# Run with environment variables
docker run --rm \
  -e LINKEDIN_ACCESS_TOKEN=your_token \
  -e LINKEDIN_ACCOUNT_ID=your_account_id \
  -v $(pwd)/output:/app/output \
  linkedin-report --campaigns active --pdf

# Run with .env file
docker run --rm \
  --env-file .env \
  -v $(pwd)/output:/app/output \
  linkedin-report --campaigns all
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  report:
    build: .
    env_file: .env
    volumes:
      - ./output:/app/output
      - ./assets:/app/assets
    command: ["--campaigns", "active", "--pdf"]
```

Run with:

```bash
docker-compose run report
```

---

## HTTPS Setup with Nginx

If you expose the report generator as a web service (e.g., via n8n webhook), set up HTTPS with nginx.

### Prerequisites

- A domain name pointing to your server
- nginx installed
- certbot installed (for Let's Encrypt)

### 1. Install nginx and certbot

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### 2. Create nginx configuration

Create `/etc/nginx/sites-available/linkedin-report`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5678;  # n8n default port
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Increase timeouts for report generation
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 3. Enable the site and obtain SSL certificate

```bash
sudo ln -s /etc/nginx/sites-available/linkedin-report /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 4. Auto-renewal

Certbot sets up auto-renewal automatically. Verify with:

```bash
sudo certbot renew --dry-run
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LINKEDIN_ACCESS_TOKEN` | Yes | - | LinkedIn Marketing API access token |
| `LINKEDIN_ACCOUNT_ID` | Yes | - | LinkedIn Ad Account ID (numeric) |
| `BRAND_NAME` | No | `LinkedIn Report Automation` | Brand name displayed in reports |
| `BRAND_TAGLINE` | No | `Automated Ad Campaign Reporting` | Tagline displayed on title slide |
| `COMPANY_NAME` | No | _(empty)_ | Company name for reports |
| `REPORT_FOOTER` | No | `Generated with LinkedIn Report Automation` | Footer text on slides |
| `SLIDE_FOOTER_ENABLED` | No | `true` | Enable/disable slide footers (`true`/`false`) |
| `THEME` | No | `linkedin` | Color theme: `linkedin`, `dark`, or `corporate` |
| `PROGRAMFILES` | No | _(system)_ | Used to locate LibreOffice on Windows |
