from abc import ABC, abstractmethod


class AnalyticsProvider(ABC):
    """Interface for portfolio analytics/reporting queries.

    In production, the operational data model (demands, projects, roadmap items) lives in
    PostgreSQL as the transactional source of truth. As the dataset grows or needs to combine
    with other enterprise sources, analytical aggregation can be offloaded to Databricks
    (Delta tables, governed via Unity Catalog) without changing any API route or frontend code —
    only the provider bound in ANALYTICS_PROVIDER changes. See databricks_provider.py.
    """

    @abstractmethod
    def get_funnel_counts(self, filters: dict) -> dict:
        """Counts of demands/projects at each funnel stage: demand, portfolio, roadmap, execution, completed."""
        raise NotImplementedError

    @abstractmethod
    def get_kpis(self, filters: dict) -> dict:
        """Top-level KPI card values for the management dashboard."""
        raise NotImplementedError

    @abstractmethod
    def get_distribution_by(self, field: str, filters: dict) -> list[dict]:
        """Project/demand counts grouped by a dimension: business_function, project_manager, priority."""
        raise NotImplementedError

    @abstractmethod
    def get_roadmap_view(self, filters: dict) -> list[dict]:
        """Scheduled roadmap items, optionally filtered, for the timeline view."""
        raise NotImplementedError

    @abstractmethod
    def get_upcoming_milestones(self, limit: int = 10) -> list[dict]:
        raise NotImplementedError
