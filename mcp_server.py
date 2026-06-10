from fastmcp import FastMCP
import db_service as db
from config import MCP_HOST, MCP_PORT, MCP_TRANSPORT, DEBUG
from datetime import datetime
import logging

mcp = FastMCP("hr-system-v2")

# -----------------------------------------------------
# DEBUG HELPER
# -----------------------------------------------------
def debug(msg: str):
    if DEBUG:
        print("DEBUG:" + msg)

# =========================================================
# EMPLOYEE PROFILE
# SKILL: employee_profile
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_profile"},
    description="""
ROLE: ANY EMPLOYEE

Get basic employee basic profile information using employee_code
"""
)
def get_employee_basic_profile(employee_code: str):
    debug(f"Invoke get_employee_basic_profile {employee_code}.")
    return db.get_employee_profile(employee_code)


# =========================================================
# EMPLOYEE PROFILE (DETAILED)
# SKILL: employee_profile
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_profile"},
    description="""
ROLE: ANY EMPLOYEE (self lookup) OR HR/ADMIN

Get full employee profile information including contacts, employment, balance, compensation.
"""
)
def get_employee_detailed_profile(employee_code: str):
    debug(f"Invoke get_employee_detailed_profile {employee_code}.")
    return db.get_employee_detailed_profile(employee_code)


# =========================================================
# GET EMPLOYEE CODE
# SKILL: employee_profile
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_profile"},
    description="""
ROLE: SYSTEM / HR ONLY

Resolve employee name into employee code.
"""
)
def get_employee_code(employee_name: str):
    debug(f"Invoke get_employee_code {employee_name}.")
    return db.get_employee_code(employee_name)


# =========================================================
# MANAGER INFO
# SKILL: employee_profile
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_profile"},
    description="""
ROLE: ANY EMPLOYEE

Get manager profile and contacts for an employee using employee_code.
"""
)
def get_employee_manager(employee_code: str):
    debug(f"Invoke get_employee_manager {employee_code}.")
    return db.get_employee_manager(employee_code)


# =========================================================
# ORG STRUCTURE
# SKILL: employee_org
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_org"},
    description="""
ROLE: ANY EMPLOYEE

Check if employee manages other employees using employee_code.
Returns boolean indicator.
"""
)
def is_a_manager(employee_code: str):
    debug(f"Invoke is_a_manager {employee_code}.")
    return db.is_a_manager(employee_code)


# =========================================================
# ORG STRUCTURE
# SKILL: employee_org
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_org"},
    description="""
ROLE: MANAGER ONLY OR HR

Get all employees reporting to a manager using employee_code.
"""
)
def get_all_managed_employees(employee_code: str):
    debug(f"Invoke get_all_managed_employees {employee_code}.")
    return db.get_all_managed_employees(employee_code)


# =========================================================
# LEAVE
# SKILL: leave
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: EMPLOYEE / MANAGER / HR

Get leave balance for an employee using employee_code.
"""
)
def get_leave_balance(employee_code: str):
    debug(f"Invoke get_leave_balance {employee_code}.")
    return db.get_leave_balance(employee_code)


# =========================================================
# LEAVE
# SKILL: leave
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: EMPLOYEE / HR

Get leave request or list of last leave requests using employee_code and optionally leave_type_id.
"""
)
def get_employee_leave_requests(
    employee_code: str,
    leave_type_id: int | None = None
):
    debug(f"Invoke get_employee_leave_requests {employee_code}, leave type id {leave_type_id}")
    return db.get_employee_leave_requests(employee_code, leave_type_id)


# =========================================================
# LEAVE
# SKILL: leave
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: MANAGER ONLY OR HR

Get pending leave requests for direct reports using manager_code.
"""
)
def get_pending_requests_for_manager(manager_code: str):
    debug(f"Invoke get_pending_requests_for_manager {manager_code}.")
    return db.get_pending_requests_for_manager(manager_code)


# =========================================================
# LEAVE
# SKILL: leave
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: EMPLOYEE ONLY

Used to Create a leave request using employee_code and other essential informations like start and end dates, and leave type, etc..
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
    
    debug(f"Invoke create_leave_request {employee_code}.")

    return db.create_leave_request(
        employee_code,
        leave_type_id,
        start_date,
        end_date,
        delegate_employee_code,
        comment
    )


# =========================================================
# LEAVE
# SKILL: leave
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: MANAGER ONLY OR HR

Approve a leave request using request_id and manager_code.
"""
)
def approve_leave_request(request_id: int, manager_code: str, manager_comment: str = None):
    debug(f"Invoke approve_leave_request by {manager_code}.")
    return db.approve_leave_request(request_id, manager_code, manager_comment)


# =========================================================
# LEAVE
# SKILL: leave
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: MANAGER ONLY OR HR

Reject a leave request using request_id and manager_code.
"""
)
def reject_leave_request(request_id: int, manager_code: str, manager_comment: str = None):
    debug(f"Invoke reject_leave_request by {manager_code}.")
    return db.reject_leave_request(request_id, manager_code, manager_comment)

# =========================================================
# LEAVE
# SKILL: LEAVE
# =========================================================
@mcp.tool(
    annotations={"skill": "leave"},
    description="""
ROLE: ANY EMPLOYEE

Get leave type info using id or name.
"""
)
def get_leave_type(leave_type_id: int = None, type_name: str = None):
    debug(f"Invoke get_leave_type for Id: {leave_type_id}, Name: {type_name}.")
    return db.get_leave_type(
        leave_type_id=leave_type_id,
        type_name=type_name
    )

# =========================================================
# POLICY
# SKILL: policy
# =========================================================
@mcp.tool(
    annotations={"skill": "policy"},
    description="""
ROLE: ANY EMPLOYEE

Search HR policies using keyword or policy name.
"""
)
def search_policies(keyword: str):
    debug(f"Invoke search_policies for {keyword}.")
    return db.search_policies(keyword)

# =========================================================
# UTIL
# =========================================================
def normalize_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")


# =========================================================
# MAIN ENTRY
# =========================================================
if __name__ == "__main__":
    print("REGISTERED TOOLS:", mcp.list_tools())
    print("Debug is set:", DEBUG)

    mcp.run(
        transport=MCP_TRANSPORT,
        host=MCP_HOST,
        port=MCP_PORT
    )