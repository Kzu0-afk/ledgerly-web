from __future__ import annotations

import os
from urllib.parse import urlparse


def buy_me_a_coffee(request):
    """
    Provide Buy Me a Coffee URL derived from environment variables.

    Priority:
    1) BMC_URL (full URL, e.g. https://www.buymeacoffee.com/yourname)
    2) BMC_USERNAME -> https://www.buymeacoffee.com/<username>
    3) Project default (owner-provided) fallback URL, if enabled

    Control visibility with:
    - BMC_ENABLED: 'true' (default) or 'false' to hide the button entirely

    Returns context key 'BMC_URL' only when a valid value is present and enabled.
    """

    enabled_raw = os.environ.get("BMC_ENABLED", "true").strip().lower()
    is_enabled = enabled_raw in {"1", "true", "yes", "on"}
    if not is_enabled:
        return {}

    env_url = os.environ.get("BMC_URL", "").strip()
    username = os.environ.get("BMC_USERNAME", "").strip()
    default_url = "https://buymeacoffee.com/kzu0"  # Owner-provided default

    bmc_url: str = ""

    if env_url:
        # Normalize and validate
        parsed = urlparse(env_url if env_url.startswith("http") else f"https://{env_url}")
        if parsed.netloc and parsed.scheme in {"http", "https"}:
            bmc_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    elif username:
        safe_username = username.replace(" ", "").strip("/")
        if safe_username:
            bmc_url = f"https://www.buymeacoffee.com/{safe_username}"
    elif default_url:
        parsed = urlparse(default_url)
        if parsed.netloc and parsed.scheme in {"http", "https"}:
            bmc_url = default_url.rstrip("/")

    return {"BMC_URL": bmc_url} if bmc_url else {}


