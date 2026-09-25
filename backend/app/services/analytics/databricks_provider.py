"""Stub Databricks-backed AnalyticsProvider — not wired up in this assessment build (no workspace
credentials available). Documents the intended production integration.

Production shape:
    - Aggregated demand/project metrics land in Delta tables (e.g. via a scheduled job or
      Structured Streaming reading from the operational PostgreSQL tables through CDC or a
      periodic batch export).
    - Governed access to those tables goes through Unity Catalog, scoped per the same RBAC
      roles used in the app (requestor / project_manager / management / admin).
    - Queries here would run via the Databricks SQL Connector for Python
      (`databricks.sql.connect(server_hostname=..., http_path=..., access_token=...)`) against
      a SQL warehouse, keeping the exact same AnalyticsProvider method signatures as
      LocalAnalyticsProvider so the API layer and frontend need zero changes to swap providers.
    - Config: set ANALYTICS_PROVIDER=databricks plus DATABRICKS_SERVER_HOSTNAME,
      DATABRICKS_HTTP_PATH and DATABRICKS_TOKEN in the environment, then register this class
      in app/services/analytics/__init__.py's _PROVIDERS map.
"""

from app.services.analytics.base import AnalyticsProvider


class DatabricksAnalyticsProvider(AnalyticsProvider):
    def get_funnel_counts(self, filters: dict) -> dict:
        raise NotImplementedError("Databricks analytics provider is not configured in this environment.")

    def get_kpis(self, filters: dict) -> dict:
        raise NotImplementedError("Databricks analytics provider is not configured in this environment.")

    def get_distribution_by(self, field: str, filters: dict) -> list[dict]:
        raise NotImplementedError("Databricks analytics provider is not configured in this environment.")

    def get_roadmap_view(self, filters: dict) -> list[dict]:
        raise NotImplementedError("Databricks analytics provider is not configured in this environment.")

    def get_upcoming_milestones(self, limit: int = 10) -> list[dict]:
        raise NotImplementedError("Databricks analytics provider is not configured in this environment.")
