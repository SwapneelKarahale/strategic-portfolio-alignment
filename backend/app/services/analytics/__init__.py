from flask import current_app

from app.services.analytics.local_provider import LocalAnalyticsProvider

_PROVIDERS = {
    "local": LocalAnalyticsProvider,
    # "databricks": DatabricksAnalyticsProvider,  # see databricks_provider.py — not wired up, no workspace credentials in this assessment
}


def get_analytics_provider():
    """Resolve the configured AnalyticsProvider. Swapping ANALYTICS_PROVIDER=databricks in config,
    once databricks_provider.py is implemented against a real workspace, requires no changes to
    any route or frontend code — everything consumes the same interface."""
    name = current_app.config.get("ANALYTICS_PROVIDER", "local")
    provider_cls = _PROVIDERS.get(name, LocalAnalyticsProvider)
    return provider_cls()
