from sqlalchemy import insert, select
from datetime import date, datetime, timezone

from db import engine
from schema import (
    employees,
    employee_contacts,
    employee_employment,
    employee_leave_balance,
    leave_types,
    leave_requests,
    policies,
    employee_compensation
)

with engine.begin() as conn:

    # ==================================================
    # EMPLOYEES (HIERARCHY)
    # ==================================================
    conn.execute(
        insert(employees),
        [
            {
                "employee_code": "CEO001",
                "full_name": "Ahmed Hassan",
                "sex": "M",
                "birthdate": date(1978, 1, 15),
                "marital_status": "married",
                "nationality": "Egyptian",
                "manager_code": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "employee_code": "MGR001",
                "full_name": "Mohamed Mourad",
                "sex": "M",
                "birthdate": date(1985, 3, 10),
                "marital_status": "married",
                "nationality": "Egyptian",
                "manager_code": "CEO001",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "employee_code": "EMP001",
                "full_name": "Osama Oransa",
                "sex": "M",
                "birthdate": date(1990, 5, 1),
                "marital_status": "single",
                "nationality": "Egyptian",
                "manager_code": "MGR001",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "employee_code": "EMP002",
                "full_name": "Sara Ali",
                "sex": "F",
                "birthdate": date(1994, 8, 20),
                "marital_status": "single",
                "nationality": "Egyptian",
                "manager_code": "MGR001",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
    )

    # ==================================================
    # CONTACTS
    # ==================================================
    conn.execute(
        insert(employee_contacts),
        [
            # EMP001
            {"employee_code": "EMP001", "contact_type": "email", "value": "osama@example.com", "is_primary": True, "created_at": datetime.now(timezone.utc)},
            {"employee_code": "EMP001", "contact_type": "phone", "value": "+201234567890", "is_primary": True, "created_at": datetime.now(timezone.utc)},

            # EMP002
            {"employee_code": "EMP002", "contact_type": "email", "value": "sara@example.com", "is_primary": True, "created_at": datetime.now(timezone.utc)},

            # MGR001
            {"employee_code": "MGR001", "contact_type": "email", "value": "mourad@example.com", "is_primary": True, "created_at": datetime.now(timezone.utc)},

            # CEO001
            {"employee_code": "CEO001", "contact_type": "email", "value": "ceo@example.com", "is_primary": True, "created_at": datetime.now(timezone.utc)},
        ]
    )

    # ==================================================
    # EMPLOYMENT
    # ==================================================
    conn.execute(
        insert(employee_employment),
        [
            {
                "employee_code": "EMP001",
                "hire_date": date(2023, 1, 1),
                "title": "Software Engineer",
                "department": "Engineering",
                "employment_type": "full-time",
                "employment_status": "active",
                "location": "Cairo"
            },
            {
                "employee_code": "EMP002",
                "hire_date": date(2023, 6, 1),
                "title": "QA Engineer",
                "department": "Engineering",
                "employment_type": "full-time",
                "employment_status": "active",
                "location": "Cairo"
            },
            {
                "employee_code": "MGR001",
                "hire_date": date(2020, 1, 1),
                "title": "Engineering Manager",
                "department": "Engineering",
                "employment_type": "full-time",
                "employment_status": "active",
                "location": "Cairo"
            },
            {
                "employee_code": "CEO001",
                "hire_date": date(2015, 1, 1),
                "title": "CEO",
                "department": "Executive",
                "employment_type": "full-time",
                "employment_status": "active",
                "location": "Cairo"
            }
        ]
    )

    # ==================================================
    # LEAVE BALANCE
    # ==================================================
    conn.execute(
        insert(employee_leave_balance),
        [
            {"employee_code": "EMP001", "annual_leave_days": 30, "sick_leave_days": 10, "parental_leave_days": 5, "last_updated": datetime.now(timezone.utc)},
            {"employee_code": "EMP002", "annual_leave_days": 25, "sick_leave_days": 10, "parental_leave_days": 5, "last_updated": datetime.now(timezone.utc)},
            {"employee_code": "MGR001", "annual_leave_days": 40, "sick_leave_days": 15, "parental_leave_days": 10, "last_updated": datetime.now(timezone.utc)},
            {"employee_code": "CEO001", "annual_leave_days": 50, "sick_leave_days": 20, "parental_leave_days": 10, "last_updated": datetime.now(timezone.utc)},
        ]
    )

    # ==================================================
    # LEAVE TYPES
    # ==================================================
    conn.execute(
        insert(leave_types),
        [
            {"type_name": "Annual Leave", "description": "Yearly vacation leave", "requires_approval": True, "max_days_per_year": 30},
            {"type_name": "Sick Leave", "description": "Medical leave", "requires_approval": False, "max_days_per_year": 10},
            {"type_name": "Parental Leave", "description": "Family leave", "requires_approval": True, "max_days_per_year": 10}
        ]
    )

    # fetch leave type ids safely
    leave_type_map = {
        row.type_name: row.id
        for row in conn.execute(select(leave_types)).fetchall()
    }

    # ==================================================
    # POLICIES
    # ==================================================
    conn.execute(
        insert(policies),
        [
            {
                "policy_name": "Annual Leave Policy",
                "category": "Leave",
                "content": "Employees get annual leave based on seniority.",
                "version": "1.0",
                "effective_date": date(2024, 1, 1)
            },
            {
                "policy_name": "Remote Work Policy",
                "category": "Work",
                "content": "Hybrid work allowed depending on manager approval.",
                "version": "1.0",
                "effective_date": date(2024, 1, 1)
            }
        ]
    )

    # ==================================================
    # COMPENSATION
    # ==================================================
    conn.execute(
        insert(employee_compensation),
        [
            {"employee_code": "EMP001", "base_salary": 3000, "currency": "USD", "allowance": 500, "effective_from": date(2024, 1, 1), "created_at": datetime.now(timezone.utc)},
            {"employee_code": "EMP002", "base_salary": 2800, "currency": "USD", "allowance": 400, "effective_from": date(2024, 1, 1), "created_at": datetime.now(timezone.utc)},
            {"employee_code": "MGR001", "base_salary": 6000, "currency": "USD", "allowance": 1000, "effective_from": date(2024, 1, 1), "created_at": datetime.now(timezone.utc)},
            {"employee_code": "CEO001", "base_salary": 12000, "currency": "USD", "allowance": 3000, "effective_from": date(2024, 1, 1), "created_at": datetime.now(timezone.utc)},
        ]
    )

    # ==================================================
    # LEAVE REQUESTS
    # ==================================================
    conn.execute(
        insert(leave_requests),
        [
            {
                "employee_code": "EMP001",
                "leave_type_id": leave_type_map["Annual Leave"],
                "start_date": date(2024, 6, 10),
                "end_date": date(2024, 6, 15),
                "delegate_employee_code": "EMP002",
                "comment": "Family vacation",
                "status": "PENDING",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "employee_code": "EMP002",
                "leave_type_id": leave_type_map["Sick Leave"],
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 3),
                "delegate_employee_code": "EMP001",
                "comment": "Medical leave",
                "status": "APPROVED",
                "approved_by_code": "MGR001",
                "created_at": datetime.now(timezone.utc)
            }
        ]
    )

print("Seed completed successfully")