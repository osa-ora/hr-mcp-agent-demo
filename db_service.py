from sqlalchemy import create_engine, select, and_, or_, asc, desc
from datetime import datetime, date, timezone
from db import engine

from schema import (
    employees,
    employee_contacts,
    employee_employment,
    employee_leave_balance,
    leave_requests,
    leave_types,
    employee_performance,
    employee_compensation,
    policies
)

# ==================================================
# INTERNAL HELPER
# ==================================================
def _get_employee(conn, emp_code: str):
    emp = conn.execute(
        select(employees)
        .where(employees.c.employee_code == emp_code)
    ).first()

    return emp._mapping if emp else None

# ==================================================
# Get Employee Code from Name
# ==================================================
from sqlalchemy import select, or_

def get_employee_code(employee_name: str):
    with engine.begin() as conn:

        # 1. FIRST: if input already looks like a code, verify it exists
        row = conn.execute(
            select(employees.c.employee_code)
            .where(employees.c.employee_code == employee_name)
        ).first()

        if row:
            return row._mapping["employee_code"]

        # 2. SECOND: match by name (case-insensitive, partial allowed)
        row = conn.execute(
            select(employees.c.employee_code)
            .where(employees.c.full_name.ilike(f"%{employee_name}%"))
        ).first()

        if row:
            return row._mapping["employee_code"]

        # 3. OPTIONAL: fallback (normalize spaces, safer matching)
        normalized = " ".join(employee_name.strip().split())

        row = conn.execute(
            select(employees.c.employee_code)
            .where(employees.c.full_name.ilike(f"%{normalized}%"))
        ).first()

        if not row:
            return None

        return row._mapping["employee_code"]
# ==================================================
# PROFILE
# ==================================================
def get_employee_profile(employee_code: str):
    with engine.begin() as conn:
        emp = _get_employee(conn, employee_code)
        return dict(emp) if emp else None

        
def get_employee_detailed_profile(employee_code: str):
    with engine.begin() as conn:

        emp = _get_employee(conn, employee_code)
        if not emp:
            return None

        code = emp["employee_code"]

        contacts = conn.execute(
            select(employee_contacts)
            .where(employee_contacts.c.employee_code == code)
        ).fetchall()

        employment = conn.execute(
            select(employee_employment)
            .where(employee_employment.c.employee_code == code)
        ).first()

        balance = conn.execute(
            select(employee_leave_balance)
            .where(employee_leave_balance.c.employee_code == code)
        ).first()

        comp = conn.execute(
            select(employee_compensation)
            .where(employee_compensation.c.employee_code == code)
        ).first()

        return {
            "employee": dict(emp),
            "contacts": [dict(c._mapping) for c in contacts],
            "employment": dict(employment._mapping) if employment else None,
            "leave_balance": dict(balance._mapping) if balance else None,
            "compensation": dict(comp._mapping) if comp else None
        }


# ==================================================
# MANAGER LOGIC
# ==================================================
def get_employee_manager(employee_code: str):
    with engine.begin() as conn:

        emp = _get_employee(conn, employee_code)
        if not emp:
            return None

        manager_code = emp.get("manager_code")
        if not manager_code:
            return None

        manager = get_employee_profile(manager_code)

        return {
            "employee_code": emp["employee_code"],
            "employee_name": emp["full_name"],
            "manager": manager
        }


def is_a_manager(employee_code: str):
    with engine.begin() as conn:

        emp = _get_employee(conn, employee_code)
        if not emp:
            return {"error": "Employee not found"}

        code = emp["employee_code"]

        managed = conn.execute(
            select(employees.c.employee_code)
            .where(employees.c.manager_code == code)
            .limit(1)
        ).first()

        return {
            "employee_code": code,
            "employee_name": emp["full_name"],
            "is_manager": managed is not None
        }


def get_all_managed_employees(employee_code: str):
    with engine.begin() as conn:

        emp = _get_employee(conn, employee_code)
        if not emp:
            return {"error": "Employee not found"}

        code = emp["employee_code"]

        rows = conn.execute(
            select(employees)
            .where(employees.c.manager_code == code)
            .order_by(employees.c.full_name)
        ).fetchall()

        return {
            "manager_code": code,
            "manager_name": emp["full_name"],
            "employees": [dict(r._mapping) for r in rows]
        }


# ==================================================
# LEAVE REQUESTS
# ==================================================
def get_employee_leave_requests(employee_code: str, leave_type_id: int | None = None):
    with engine.begin() as conn:

        query = (
            select(leave_requests)
            .where(leave_requests.c.employee_code == employee_code)
            .order_by(desc(leave_requests.c.created_at))
            .limit(5)
        )

        if leave_type_id is not None:
            query = query.where(
                leave_requests.c.leave_type_id == leave_type_id
            )

        rows = conn.execute(query).fetchall()

        return [dict(r._mapping) for r in rows]

# Get single leave request by ID
def get_employee_leave_request(request_id: int):
    with engine.begin() as conn:
        row = conn.execute(
            select(leave_requests)
            .where(leave_requests.c.id == request_id)
        ).first()
        return dict(row._mapping) if row else None

# Get pending leave requests for a manager
def get_pending_requests_for_manager(manager_code: str):
    with engine.begin() as conn:

        sub = select(employees.c.employee_code).where(
            employees.c.manager_code == manager_code
        )

        rows = conn.execute(
            select(leave_requests)
            .where(
                and_(
                    leave_requests.c.employee_code.in_(sub),
                    leave_requests.c.status == "PENDING"
                )
            )
            .order_by(asc(leave_requests.c.created_at))  
            .limit(10)
        ).fetchall()

        return [dict(r._mapping) for r in rows]


# ==================================================
# LEAVE BALANCE
# ==================================================
def get_leave_balance(employee_code: str):
    with engine.begin() as conn:
        row = conn.execute(
            select(employee_leave_balance)
            .where(employee_leave_balance.c.employee_code == employee_code)
        ).first()
        return dict(row._mapping) if row else None
        
# ==================================================
# PERFORMANCE
# ==================================================
def get_employee_performance(employee_code: str, year: int = None):
    with engine.begin() as conn:

        q = select(employee_performance).where(
            employee_performance.c.employee_code == employee_code
        )

        if year:
            q = q.where(employee_performance.c.performance_year == year)

        rows = conn.execute(q).fetchall()
        return [dict(r._mapping) for r in rows]


# ==================================================
# COMPENSATION
# ==================================================
def get_employee_compensation(employee_code: str):
    with engine.begin() as conn:
        row = conn.execute(
            select(employee_compensation)
            .where(employee_compensation.c.employee_code == employee_code)
        ).first()
        if not row:
            raise ValueError("Employee code not found")
        return dict(row._mapping) if row else None


# ==================================================
# POLICIES
# ==================================================

def search_policies(keyword: str):
    keyword = f"%{keyword}%"

    with engine.begin() as conn:
        stmt = select(policies).where(
            or_(
                policies.c.policy_name.ilike(keyword),
                policies.c.content.ilike(keyword)
            )
        )

        rows = conn.execute(stmt).fetchall()

        return [dict(r._mapping) for r in rows]


# ==================================================
# LEAVE CREATION
# ==================================================
def create_leave_request(
    employee_code,
    leave_type_id,
    start_date,
    end_date,
    delegate_employee_code=None,
    comment=""
):

    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date).date()
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date).date()

    if start_date > end_date:
        raise ValueError("Invalid range")

    if start_date < date.today():
        raise ValueError("Start date must be future")

    total_days = (end_date - start_date).days + 1

    with engine.begin() as conn:

        balance = conn.execute(
            select(employee_leave_balance)
            .where(employee_leave_balance.c.employee_code == employee_code)
        ).mappings().first()

        if not balance:
            raise ValueError("No balance")

        # FIX: validate by leave type
        if leave_type_id == 1:
            available = balance["annual_leave_days"]
        elif leave_type_id == 2:
            available = balance["sick_leave_days"]
        elif leave_type_id == 3:
            available = balance["parental_leave_days"]
        else:
            raise ValueError("Unknown leave type")

        if total_days > available:
            raise ValueError("Insufficient leave balance")

        result = conn.execute(
            leave_requests.insert().values(
                employee_code=employee_code,
                leave_type_id=leave_type_id,
                start_date=start_date,
                end_date=end_date,
                delegate_employee_code=delegate_employee_code,
                comment=comment,
                status="PENDING",
                created_at=datetime.now(timezone.utc)
            )
        )

        return result.inserted_primary_key[0]


# ==================================================
# LEAVE ACTION VALIDATION
# ==================================================
def validate_leave_request_action(conn, request_id: int, manager_code: str):
    req = conn.execute(
        select(leave_requests)
        .where(leave_requests.c.id == request_id)
    ).first()

    if not req:
        return {"error": "Not found"}

    req = dict(req._mapping)

    if req["status"] != "PENDING":
        return {"error": "Already processed"}

    emp = conn.execute(
        select(employees.c.manager_code)
        .where(employees.c.employee_code == req["employee_code"])
    ).first()
    if not emp:
        return {"error": "Employee not found"}

    if emp[0] != manager_code:
        return {"error": "Not authorized"}

    return req


# ==================================================
# APPROVE
# ==================================================
def approve_leave_request(request_id: int, manager_code: str, comment: str = None):
    with engine.begin() as conn:

        req = validate_leave_request_action(conn, request_id, manager_code)

        if isinstance(req, dict) and "error" in req:
            return req

        employee_code = req["employee_code"]
        leave_type_id = req["leave_type_id"]

        start_date = req["start_date"]
        end_date = req["end_date"]

        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        total_days = (end_date - start_date).days + 1

        adjust_leave_balance(
            conn,
            employee_code,
            leave_type_id,
            total_days
        )

        conn.execute(
            leave_requests.update()
            .where(leave_requests.c.id == request_id)
            .values(
                status="APPROVED",
                approved_by_code=manager_code,
                approved_at=datetime.now(timezone.utc),
                manager_comment=comment
            )
        )

        return {"status": "APPROVED", "request_id": request_id}


# ==================================================
# REJECT
# ==================================================
def reject_leave_request(request_id: int, manager_code: str, comment: str = None):
    with engine.begin() as conn:

        req = validate_leave_request_action(conn, request_id, manager_code)

        if isinstance(req, dict) and "error" in req:
            return req

        conn.execute(
            leave_requests.update()
            .where(leave_requests.c.id == request_id)
            .values(
                status="REJECTED",
                approved_by_code=manager_code,
                approved_at=datetime.now(timezone.utc),
                manager_comment=comment
            )
        )

        return {"status": "REJECTED", "request_id": request_id}


# ==================================================
# BALANCE ADJUSTMENT
# ==================================================
def adjust_leave_balance(conn, employee_code: str, leave_type_id: int, days: int):

    row = conn.execute(
        select(employee_leave_balance)
        .where(employee_leave_balance.c.employee_code == employee_code)
    ).first()

    if not row:
        raise ValueError("No balance")

    bal = dict(row._mapping)

    if leave_type_id == 1:
        field = "annual_leave_days"
    elif leave_type_id == 2:
        field = "sick_leave_days"
    elif leave_type_id == 3:
        field = "parental_leave_days"
    else:
        raise ValueError("Unknown leave type")

    new_val = bal[field] - days

    if new_val < 0:
        raise ValueError("Insufficient balance")

    conn.execute(
        employee_leave_balance.update()
        .where(employee_leave_balance.c.employee_code == employee_code)
        .values(
            **{field: new_val},
            last_updated=datetime.now(timezone.utc)
        )
    )

# ==================================================
# LEAVE TYPE RESOLVER (ID or NAME → FULL OBJECT)
# ==================================================
def get_leave_type(leave_type_id: int = None, type_name: str = None):
    with engine.begin() as conn:

        if leave_type_id is None and type_name is None:
            raise ValueError("Either leave_type_id or type_name must be provided")

        q = select(leave_types)

        if leave_type_id is not None:
            q = q.where(leave_types.c.id == leave_type_id)

        if type_name is not None:
            q = q.where(leave_types.c.type_name.ilike(type_name))

        row = conn.execute(q).first()

        if not row:
            return None

        return dict(row._mapping)
