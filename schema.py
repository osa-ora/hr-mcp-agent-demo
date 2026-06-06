# CREATE DATABASE hrdb;

from sqlalchemy import *

metadata = MetaData()

# ----------------------------
# EMPLOYEES (CORE ENTITY)
# ----------------------------
employees = Table(
    "employees",
    metadata,

    # Business identity (PRIMARY KEY NOW)
    Column("employee_code", String(50), primary_key=True),

    Column("full_name", String(200), nullable=False),

    Column("sex", String(20)),
    Column("birthdate", Date),
    Column("marital_status", String(50)),
    Column("nationality", String(100)),

    # Business relationship (no FK constraint by design)
    Column("manager_code", String(50), nullable=True),

    Column("created_at", DateTime),
    Column("updated_at", DateTime)
)


# ----------------------------
# EMPLOYEE CONTACTS (1 → N)
# ----------------------------
employee_contacts = Table(
    "employee_contacts",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("employee_code", String(50), ForeignKey("employees.employee_code"), nullable=False),

    Column("contact_type", String(50), nullable=False),  # phone, email, address

    Column("value", Text, nullable=False),

    Column("is_primary", Boolean, default=False),

    Column("created_at", DateTime)
)


# ----------------------------
# EMPLOYMENT DETAILS
# ----------------------------
employee_employment = Table(
    "employee_employment",
    metadata,

    Column("employee_code", String(50), ForeignKey("employees.employee_code"), primary_key=True),

    Column("hire_date", Date),

    Column("last_working_date", Date),

    Column("title", String(200)),

    Column("department", String(100)),

    Column("employment_type", String(50)),  # full-time, part-time, contractor

    Column("employment_status", String(50)),  # active, inactive, terminated

    Column("location", String(200))
)


# ----------------------------
# LEAVE TYPES
# ----------------------------
leave_types = Table(
    "leave_types",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("type_name", String(100), unique=True, nullable=False),

    Column("description", Text),

    Column("requires_approval", Boolean, default=True),

    Column("max_days_per_year", Integer)
)


# ----------------------------
# LEAVE BALANCE (1 → 1 per employee)
# ----------------------------
employee_leave_balance = Table(
    "employee_leave_balance",
    metadata,

    Column("employee_code", String(50), ForeignKey("employees.employee_code"), primary_key=True),

    Column("annual_leave_days", Integer, default=0),

    Column("sick_leave_days", Integer, default=0),

    Column("parental_leave_days", Integer, default=0),

    Column("last_updated", DateTime)
)


# ----------------------------
# LEAVE REQUESTS
# ----------------------------
leave_requests = Table(
    "leave_requests",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("employee_code", String(50), ForeignKey("employees.employee_code"), nullable=False),

    Column("leave_type_id", Integer, ForeignKey("leave_types.id"), nullable=False),

    Column("start_date", Date, nullable=False),

    Column("end_date", Date, nullable=False),

    Column("delegate_employee_code", String(50), ForeignKey("employees.employee_code")),

    Column("comment", Text),
    Column("manager_comment", Text),

    Column("status", String(50), default="PENDING"),

    Column("approved_by_code", String(50), ForeignKey("employees.employee_code")),

    Column("approved_at", DateTime),

    Column("created_at", DateTime)
)


# ----------------------------
# PERFORMANCE
# ----------------------------
employee_performance = Table(
    "employee_performance",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("employee_code", String(50), ForeignKey("employees.employee_code"), nullable=False),

    Column("performance_year", Integer, nullable=False),

    Column("performance_quarter", Integer, nullable=False),

    Column("performance_score", Numeric(5, 2)),

    Column("performance_comment", Text),

    Column("reviewed_by_code", String(50), ForeignKey("employees.employee_code")),

    Column("created_at", DateTime)
)


# ----------------------------
# COMPENSATION
# ----------------------------
employee_compensation = Table(
    "employee_compensation",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("employee_code", String(50), ForeignKey("employees.employee_code"), nullable=False),

    Column("base_salary", Numeric(18, 2)),

    Column("currency", String(10)),

    Column("allowance", Numeric(18, 2)),

    Column("effective_from", Date),

    Column("created_at", DateTime)
)


# ----------------------------
# POLICIES
# ----------------------------
policies = Table(
    "policies",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("policy_name", String(200), unique=True, nullable=False),

    Column("category", String(100)),

    Column("content", Text),

    Column("version", String(20)),

    Column("effective_date", Date)
)


# ----------------------------
# APPROVAL AUDIT LOG (CRITICAL FOR AGENTS)
# ----------------------------
approval_history = Table(
    "approval_history",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("entity_type", String(50), nullable=False),
    Column("entity_id", Integer, nullable=False),

    Column("action", String(50), nullable=False),

    Column("performed_by_code", String(50), ForeignKey("employees.employee_code")),

    Column("comment", Text),

    Column("created_at", DateTime)
)