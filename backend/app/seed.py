"""Seed the database with realistic-but-fictional demo data so the dashboard is meaningful
immediately after startup. Run with: `flask --app wsgi seed`."""

import random
from datetime import date, timedelta

from app.extensions import db
from app.models.collaboration import AuditLog
from app.models.demand import Demand, DemandReview
from app.models.enums import DemandStatus, Priority, ProjectHealth, ProjectStatus, RequestType, Role
from app.models.project import Capability, Milestone, Project, ProjectCapability, Requirement, RoadmapItem
from app.models.user import BusinessFunction, User

DEMO_PASSWORD = "Password123!"

BUSINESS_FUNCTIONS = ["Finance", "Sales & Marketing", "Operations", "Human Resources", "Supply Chain", "IT"]
CAPABILITIES = ["Data Engineering", "Power BI", "Application Development", "AI/ML", "Other"]

DEMAND_TITLES = [
    "Customer 360 Analytics Platform",
    "Finance Reporting Automation",
    "Power BI Sales Dashboard",
    "Data Lake Migration",
    "ML Model for Churn Prediction",
    "HR Analytics Dashboard",
    "Marketing Campaign Insights",
    "Supply Chain Visibility Tool",
    "Invoice Processing Automation",
    "Employee Attrition Predictor",
    "Regional Sales Forecasting",
    "Vendor Performance Scorecard",
    "Inventory Optimization Model",
    "Customer Support Ticket Analytics",
    "Procurement Spend Dashboard",
    "Quarterly Board Reporting Automation",
    "Social Media Sentiment Tracker",
    "Warehouse Capacity Planning Tool",
    "Product Return Analysis",
    "Compliance Audit Tracker",
    "Real-Time Fraud Detection",
    "Executive KPI Dashboard",
    "Contract Renewal Reminder System",
    "Logistics Route Optimization",
    "Talent Acquisition Funnel Analytics",
    "Price Elasticity Model",
    "Customer Lifetime Value Scoring",
    "Store Performance Benchmarking",
]

PROBLEM_STATEMENTS = [
    "Teams currently rely on manual spreadsheet consolidation, which is slow and error-prone.",
    "There is no single source of truth for this metric today, leading to conflicting reports.",
    "The current process takes several days each month and does not scale with growth.",
    "Leadership lacks real-time visibility into this area and relies on stale monthly reports.",
    "Data is scattered across multiple systems with no unified view for decision-making.",
]


def _random_date_within(days_back: int) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


def _random_future_date(days_forward: int) -> date:
    return date.today() + timedelta(days=random.randint(7, days_forward))


def run_seed() -> None:
    if BusinessFunction.query.first() is not None:
        print("Seed data already present — skipping.")
        return

    business_functions = []
    for name in BUSINESS_FUNCTIONS:
        bf = BusinessFunction(name=name)
        db.session.add(bf)
        business_functions.append(bf)

    capabilities = []
    for name in CAPABILITIES:
        cap = Capability(name=name)
        db.session.add(cap)
        capabilities.append(cap)

    db.session.flush()

    def make_user(name, email, role, bf=None):
        user = User(name=name, email=email, role=role, business_function_id=bf.id if bf else None, active=True)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        return user

    admin = make_user("Ava Administrator", "admin@globaldata.example", Role.ADMIN)
    management_users = [
        make_user("Sarah Miller", "sarah.miller@globaldata.example", Role.MANAGEMENT),
        make_user("David Chen", "david.chen@globaldata.example", Role.MANAGEMENT),
    ]
    pm_users = [
        make_user("Priya Nair", "priya.nair@globaldata.example", Role.PROJECT_MANAGER),
        make_user("John Doe", "john.doe@globaldata.example", Role.PROJECT_MANAGER),
        make_user("Elena Petrova", "elena.petrova@globaldata.example", Role.PROJECT_MANAGER),
        make_user("Marcus Webb", "marcus.webb@globaldata.example", Role.PROJECT_MANAGER),
    ]
    requestor_users = [
        make_user(f"Requestor {bf.name.split()[0]}", f"requestor.{bf.name.lower().split()[0]}@globaldata.example", Role.REQUESTOR, bf)
        for bf in business_functions
    ]
    db.session.flush()

    demand_statuses_pool = (
        [DemandStatus.DRAFT] * 3
        + [DemandStatus.SUBMITTED] * 4
        + [DemandStatus.UNDER_REVIEW] * 5
        + [DemandStatus.CLARIFICATION_REQUIRED] * 3
        + [DemandStatus.VALIDATED] * 3
        + [DemandStatus.APPROVED] * 8
        + [DemandStatus.REJECTED] * 2
    )
    random.shuffle(demand_statuses_pool)

    demands = []
    for i, title in enumerate(DEMAND_TITLES):
        status = demand_statuses_pool[i % len(demand_statuses_pool)]
        requestor = random.choice(requestor_users)
        demand = Demand(
            title=title,
            business_function_id=requestor.business_function_id,
            requestor_id=requestor.id,
            problem_statement=random.choice(PROBLEM_STATEMENTS),
            business_need="Improve decision speed and reduce manual effort for this business area.",
            support_required=random.choice(["Data Engineering", "Power BI", "Application Development", "AI/ML"]),
            request_type=random.choice(list(RequestType)),
            priority=random.choice(list(Priority)),
            expected_timeline=random.choice(["Q1 2026", "Q2 2026", "Q3 2026", "March/April 2026"]),
            status=status,
            created_at=_random_date_within(120),
        )
        db.session.add(demand)
        demands.append(demand)
    db.session.flush()

    for demand in demands:
        if demand.status == DemandStatus.DRAFT:
            continue
        reviewer = random.choice(pm_users + management_users)
        db.session.add(
            DemandReview(demand_id=demand.id, reviewer_id=reviewer.id, action=demand.status.value, comments="Reviewed per standard intake process.")
        )
        db.session.add(
            AuditLog(user_id=reviewer.id, action="reviewed demand", resource_type="demand", resource_id=demand.id, new_value=demand.status.value)
        )

    approved_demands = [d for d in demands if d.status == DemandStatus.APPROVED]
    project_status_pool = (
        [ProjectStatus.PORTFOLIO] * 3
        + [ProjectStatus.PLANNED] * 2
        + [ProjectStatus.IN_PROGRESS] * 5
        + [ProjectStatus.AT_RISK] * 2
        + [ProjectStatus.BLOCKED] * 1
        + [ProjectStatus.COMPLETED] * 3
    )
    random.shuffle(project_status_pool)

    quarters = ["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]

    for i, demand in enumerate(approved_demands):
        target_status = project_status_pool[i % len(project_status_pool)]
        pm = random.choice(pm_users)
        health = (
            ProjectHealth.AT_RISK
            if target_status == ProjectStatus.AT_RISK
            else ProjectHealth.BLOCKED
            if target_status == ProjectStatus.BLOCKED
            else ProjectHealth.ON_TRACK
        )
        project = Project(
            demand_id=demand.id,
            name=demand.title,
            description=f"Portfolio project delivering: {demand.title}.",
            business_objective=demand.business_need,
            project_manager_id=pm.id,
            status=ProjectStatus.PORTFOLIO,  # set correctly below, after requirements/roadmap are attached
            priority=demand.priority,
            health=health,
            estimated_effort=random.choice(["2 sprints", "1 quarter", "6 weeks", "3 months"]),
        )
        db.session.add(project)
        db.session.flush()

        db.session.add(Requirement(project_id=project.id, requirement_text="Define source data feeds and refresh cadence.", category="Data"))
        db.session.add(Requirement(project_id=project.id, requirement_text="Design and validate the target dashboard/report layout.", category="UX"))

        for cap in random.sample(capabilities, k=random.randint(1, 2)):
            db.session.add(ProjectCapability(project_id=project.id, capability_id=cap.id, effort_estimate="4-6 weeks"))

        needs_roadmap = target_status != ProjectStatus.PORTFOLIO
        if needs_roadmap:
            start = _random_date_within(60) if target_status in (ProjectStatus.IN_PROGRESS, ProjectStatus.AT_RISK, ProjectStatus.BLOCKED, ProjectStatus.COMPLETED) else _random_future_date(90)
            end = start + timedelta(days=random.randint(45, 120))
            db.session.add(
                RoadmapItem(
                    project_id=project.id,
                    quarter=random.choice(quarters),
                    sequence=i,
                    planned_start=start,
                    planned_end=end if target_status != ProjectStatus.COMPLETED else start + timedelta(days=30),
                )
            )
            project.start_date = start
            project.target_date = end

        project.status = target_status

        if target_status in (ProjectStatus.IN_PROGRESS, ProjectStatus.AT_RISK, ProjectStatus.BLOCKED, ProjectStatus.COMPLETED):
            m_status = "Completed" if target_status == ProjectStatus.COMPLETED else random.choice(["Planned", "In Progress", "At Risk"])
            db.session.add(
                Milestone(
                    project_id=project.id,
                    name="Requirements sign-off",
                    due_date=_random_date_within(20) if target_status == ProjectStatus.COMPLETED else _random_future_date(30),
                    status=m_status,
                    owner_id=pm.id,
                )
            )
            db.session.add(
                Milestone(
                    project_id=project.id,
                    name="UAT complete",
                    due_date=_random_future_date(60),
                    status="Completed" if target_status == ProjectStatus.COMPLETED else "Planned",
                    owner_id=pm.id,
                )
            )

        db.session.add(
            AuditLog(user_id=pm.id, action="converted demand to project", resource_type="demand", resource_id=demand.id, new_value=f"project:{project.id}")
        )

    db.session.commit()
    print(f"Seeded {len(business_functions)} business functions, {len(capabilities)} capabilities, "
          f"{1 + len(management_users) + len(pm_users) + len(requestor_users)} users, "
          f"{len(demands)} demands, {len(approved_demands)} projects.")
    print(f"Demo login password for every seeded user: {DEMO_PASSWORD}")
