"""Shared configuration for paths, seeds, and dry-run defaults."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
PROJECTS_ROOT = REPO_ROOT / "projects"

DEFAULT_RANDOM_SEED = 42
DEFAULT_DRY_RUN = True

DEFAULT_SFDC_USERNAME = "portfolio@example.com"
DEFAULT_SFDC_PASSWORD = "placeholder-password"
DEFAULT_SFDC_SECURITY_TOKEN = "placeholder-token"
DEFAULT_SFDC_DOMAIN = "login"

DEFAULT_CLAY_API_KEY = "clay-placeholder-key"
DEFAULT_CLAY_BASE_URL = "https://api.clay.com/v1"

DEFAULT_PARABOLA_API_KEY = "parabola-placeholder-key"
DEFAULT_PARABOLA_BASE_URL = "https://api.parabola.io/v1"

DEFAULT_SLACK_BOT_TOKEN = "xoxb-placeholder-token"
DEFAULT_SLACK_CHANNEL = "#gtm-automation"

DEFAULT_USAGE_PROVIDER = "datadog_rum"
DEFAULT_USAGE_SITE = "datadoghq.com"

DATA_FOUNDATIONS_DIR = PROJECTS_ROOT / "01_gtm_data_foundations"
DATA_DIR = DATA_FOUNDATIONS_DIR / "data"
DATA_OUTPUT_DIR = DATA_FOUNDATIONS_DIR / "output"

TERRITORY_BALANCER_DIR = PROJECTS_ROOT / "02_territory_balancer"
FREETIER_ALERT_DIR = PROJECTS_ROOT / "03_freetier_usage_alert"
LEAD_ENRICHMENT_DIR = PROJECTS_ROOT / "04_lead_enrichment"
RENEWAL_AUTOMATION_DIR = PROJECTS_ROOT / "05_am_renewal_form_automation"
MARKETING_ATTRIBUTION_DIR = PROJECTS_ROOT / "06_marketing_attribution_and_funnel_model"

SALESFORCE_CONFIG = {
    "username": os.getenv("SFDC_USERNAME", DEFAULT_SFDC_USERNAME),
    "password": os.getenv("SFDC_PASSWORD", DEFAULT_SFDC_PASSWORD),
    "security_token": os.getenv("SFDC_SECURITY_TOKEN", DEFAULT_SFDC_SECURITY_TOKEN),
    "domain": os.getenv("SFDC_DOMAIN", DEFAULT_SFDC_DOMAIN),
}

CLAY_CONFIG = {
    "api_key": os.getenv("CLAY_API_KEY", DEFAULT_CLAY_API_KEY),
    "base_url": os.getenv("CLAY_BASE_URL", DEFAULT_CLAY_BASE_URL),
}

PARABOLA_CONFIG = {
    "api_key": os.getenv("PARABOLA_API_KEY", DEFAULT_PARABOLA_API_KEY),
    "base_url": os.getenv("PARABOLA_BASE_URL", DEFAULT_PARABOLA_BASE_URL),
}

SLACK_CONFIG = {
    "bot_token": os.getenv("SLACK_BOT_TOKEN", DEFAULT_SLACK_BOT_TOKEN),
    "default_channel": os.getenv("SLACK_DEFAULT_CHANNEL", DEFAULT_SLACK_CHANNEL),
}

USAGE_EVENTS_CONFIG = {
    "provider": os.getenv("USAGE_PROVIDER", DEFAULT_USAGE_PROVIDER),
    "site": os.getenv("USAGE_SITE", DEFAULT_USAGE_SITE),
}

DATASET_FILENAMES = {
    "owners": "owners.csv",
    "accounts": "accounts.csv",
    "leads": "leads.csv",
    "opportunities": "opportunities.csv",
    "product_usage_events": "product_usage_events.csv",
}
