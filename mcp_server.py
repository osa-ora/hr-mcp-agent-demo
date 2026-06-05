from fastmcp import FastMCP
import db_service as db
from datetime import datetime

mcp = FastMCP("hr-system")


# =========================================================
# EMPLOYEE PROFILE (ROLE: ANY EMPLOYEE)
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE

Get basic employee profile using employee_identifier (employee_code or partial name).
"""
)
def get_employee_profile(employee_identifier: str):
    return db.get_employee_profile(employee_identifier)


# =========================================================
# EMPLOYEE PROFILE (DETAILED)
# ROLE: ANY EMPLOYEE (self) OR HR/ADMIN
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE (self lookup) OR HR/ADMIN

Get full employee profile including contacts, employment, balance, compensation.
"""
)
def get_employee_detailed_profile(employee_identifier: str):
    return db.get_employee_detailed_profile(employee_identifier)


# =========================================================
# GET EMPLOYEE ID
# ROLE: SYSTEM / INTERNAL / HR
# =========================================================
@mcp.tool(
    description="""
ROLE: SYSTEM / HR ONLY

Resolve employee name into employee code.
"""
)
def get_employee_code(employee_identifier: str):
    return db.get_employee_code(employee_identifier)


# =========================================================
# MANAGER INFO
# ROLE: ANY EMPLOYEE (self lookup)
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE

Get manager profile and contacts for an employee using employee_identifier.
"""
)
def get_employee_manager(employee_identifier: str):
    return db.get_employee_manager(employee_identifier)


# =========================================================
# IS MANAGER CHECK
# ROLE: ANY EMPLOYEE (informational)
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE

Check if employee manages other employees.
Returns boolean indicator.
"""
)
def is_a_manager(employee_identifier: str):
    return db.is_a_manager(employee_identifier)


# =========================================================
# MANAGED EMPLOYEES LIST
# ROLE: MANAGER ONLY (or HR)
# =========================================================
@mcp.tool(
    description="""
ROLE: MANAGER ONLY OR HR

Get all employees reporting to a manager using employee_identifier.
"""
)
def get_all_managed_employees(employee_identifier: str):
    return db.get_all_managed_employees(employee_identifier)


# =========================================================
# LEAVE BALANCE
# ROLE: ANY EMPLOYEE (self) OR MANAGER (direct reports) OR HR
# =========================================================
@mcp.tool(
    description="""
ROLE: EMPLOYEE / MANAGER / HR

Get leave balance for an employee using employee_code.
"""
)
def get_leave_balance(employee_code: str):
    return db.get_leave_balance(employee_code)


# =========================================================
# LEAVE REQUESTS (EMPLOYEE)
# ROLE: SELF ONLY / HR
# =========================================================
@mcp.tool(
    description="""
ROLE: EMPLOYEE (self) OR HR

Get all leave requests for an employee using employee_code.
"""
)
def get_employee_leave_requests(employee_code: str):
    return db.get_employee_leave_requests(employee_code)


# =========================================================
# FILTER LEAVE REQUESTS
# ROLE: EMPLOYEE / HR
# =========================================================
@mcp.tool(
    description="""
ROLE: EMPLOYEE / HR

Filter leave requests by employee_code and leave_type_id.
"""
)
def filter_employee_leave_requests(employee_code: str, leave_type_id: int):
    return db.filter_employee_leave_requests(employee_code, leave_type_id)


# =========================================================
# MANAGER PENDING REQUESTS
# ROLE: MANAGER ONLY / HR
# =========================================================
@mcp.tool(
    description="""
ROLE: MANAGER ONLY OR HR

Get pending leave requests for direct reports using manager employee_code.
"""
)
def get_pending_requests_for_manager(manager_code: str):
    return db.get_pending_requests_for_manager(manager_code)


# =========================================================
# CREATE LEAVE REQUEST
# ROLE: EMPLOYEE ONLY (self-service)
# =========================================================
@mcp.tool(
    description="""
ROLE: EMPLOYEE ONLY

Create a leave request using employee_code.
Dates must be YYYY-MM-DD.
"""
)
def create_leave_request(
    employee_code: str,
    leave_type_id: int,
    start_date: str,
    end_date: str,
    delegate_employee_code: str = None,
    comment: str = ""
):
    start_date = normalize_date(start_date)
    end_date = normalize_date(end_date)

    return db.create_leave_request(
        employee_code,
        leave_type_id,
        start_date,
        end_date,
        delegate_employee_code,
        comment
    )


def normalize_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")


# =========================================================
# APPROVE LEAVE REQUEST
# ROLE: MANAGER ONLY / HR
# =========================================================
@mcp.tool(
    description="""
ROLE: MANAGER ONLY OR HR

Approve a leave request using request_id and manager_code.
"""
)
def approve_leave_request(request_id: int, manager_code: str, manager_comment: str = None):
    return db.approve_leave_request(request_id, manager_code, manager_comment)


# =========================================================
# REJECT LEAVE REQUEST
# ROLE: MANAGER ONLY / HR
# =========================================================
@mcp.tool(
    description="""
ROLE: MANAGER ONLY OR HR

Reject a leave request using request_id and manager_code.
"""
)
def reject_leave_request(request_id: int, manager_code: str, manager_comment: str = None):
    return db.reject_leave_request(request_id, manager_code, manager_comment)


# =========================================================
# POLICY SEARCH
# ROLE: ANY EMPLOYEE
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE

Search HR policies using keyword.
"""
)
def search_policies(keyword: str):
    return db.search_policies(keyword)


# =========================================================
# LEAVE TYPE LOOKUP
# ROLE: ANY EMPLOYEE
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE

Get leave type info using id or name.
"""
)
def get_leave_type(leave_type_id: int = None, type_name: str = None):
    return db.get_leave_type(leave_type_id=leave_type_id, type_name=type_name)


# =========================================================
# MAIN ENTRY
# =========================================================
if __name__ == "__main__":
    print("REGISTERED TOOLS:", mcp.list_tools())
    mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=8000
    )