-- =========================================================
-- DATABASE
-- =========================================================
CREATE DATABASE hrdb;

-- connect to it:
-- \c hrdb;
-- then execute the creation
-- or run the following: 
-- curl -s https://your-host/schema.sql | psql -U postgres -d hrdb
-- curl -s https://your-host/load_sample_data.sql | psql -U postgres -d hrdb
-- =========================================================
-- EMPLOYEES (CORE ENTITY)
-- =========================================================
CREATE TABLE employees (
    employee_code VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,

    sex VARCHAR(20),
    birthdate DATE,
    marital_status VARCHAR(50),
    nationality VARCHAR(100),

    manager_code VARCHAR(50),

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- =========================================================
-- EMPLOYEE CONTACTS
-- =========================================================
CREATE TABLE employee_contacts (
    id SERIAL PRIMARY KEY,

    employee_code VARCHAR(50) NOT NULL,
    contact_type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP,

    CONSTRAINT fk_employee_contacts_employee
        FOREIGN KEY (employee_code)
        REFERENCES employees(employee_code)
        ON DELETE CASCADE
);

-- =========================================================
-- EMPLOYMENT DETAILS
-- =========================================================
CREATE TABLE employee_employment (
    employee_code VARCHAR(50) PRIMARY KEY,

    hire_date DATE,
    last_working_date DATE,

    title VARCHAR(200),
    department VARCHAR(100),

    employment_type VARCHAR(50),
    employment_status VARCHAR(50),

    location VARCHAR(200),

    CONSTRAINT fk_employee_employment_employee
        FOREIGN KEY (employee_code)
        REFERENCES employees(employee_code)
        ON DELETE CASCADE
);

-- =========================================================
-- LEAVE TYPES
-- =========================================================
CREATE TABLE leave_types (
    id SERIAL PRIMARY KEY,

    type_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,

    requires_approval BOOLEAN DEFAULT TRUE,
    max_days_per_year INTEGER
);

-- =========================================================
-- LEAVE BALANCE
-- =========================================================
CREATE TABLE employee_leave_balance (
    employee_code VARCHAR(50) PRIMARY KEY,

    annual_leave_days INTEGER DEFAULT 0,
    sick_leave_days INTEGER DEFAULT 0,
    parental_leave_days INTEGER DEFAULT 0,

    last_updated TIMESTAMP,

    CONSTRAINT fk_leave_balance_employee
        FOREIGN KEY (employee_code)
        REFERENCES employees(employee_code)
        ON DELETE CASCADE
);

-- =========================================================
-- LEAVE REQUESTS
-- =========================================================
CREATE TABLE leave_requests (
    id SERIAL PRIMARY KEY,

    employee_code VARCHAR(50) NOT NULL,
    leave_type_id INTEGER NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    delegate_employee_code VARCHAR(50),

    comment TEXT,
    manager_comment TEXT,

    status VARCHAR(50) DEFAULT 'PENDING',

    approved_by_code VARCHAR(50),
    approved_at TIMESTAMP,

    created_at TIMESTAMP,

    CONSTRAINT fk_leave_employee
        FOREIGN KEY (employee_code)
        REFERENCES employees(employee_code),

    CONSTRAINT fk_leave_delegate
        FOREIGN KEY (delegate_employee_code)
        REFERENCES employees(employee_code),

    CONSTRAINT fk_leave_approved_by
        FOREIGN KEY (approved_by_code)
        REFERENCES employees(employee_code),

    CONSTRAINT fk_leave_type
        FOREIGN KEY (leave_type_id)
        REFERENCES leave_types(id)
);

-- =========================================================
-- PERFORMANCE
-- =========================================================
CREATE TABLE employee_performance (
    id SERIAL PRIMARY KEY,

    employee_code VARCHAR(50) NOT NULL,

    performance_year INTEGER NOT NULL,
    performance_quarter INTEGER NOT NULL,

    performance_score NUMERIC(5,2),
    performance_comment TEXT,

    reviewed_by_code VARCHAR(50),

    created_at TIMESTAMP,

    CONSTRAINT fk_perf_employee
        FOREIGN KEY (employee_code)
        REFERENCES employees(employee_code),

    CONSTRAINT fk_perf_reviewed_by
        FOREIGN KEY (reviewed_by_code)
        REFERENCES employees(employee_code)
);

-- =========================================================
-- COMPENSATION
-- =========================================================
CREATE TABLE employee_compensation (
    id SERIAL PRIMARY KEY,

    employee_code VARCHAR(50) NOT NULL,

    base_salary NUMERIC(18,2),
    currency VARCHAR(10),
    allowance NUMERIC(18,2),

    effective_from DATE,
    created_at TIMESTAMP,

    CONSTRAINT fk_comp_employee
        FOREIGN KEY (employee_code)
        REFERENCES employees(employee_code)
);

-- =========================================================
-- POLICIES
-- =========================================================
CREATE TABLE policies (
    id SERIAL PRIMARY KEY,

    policy_name VARCHAR(200) UNIQUE NOT NULL,
    category VARCHAR(100),
    content TEXT,
    version VARCHAR(20),
    effective_date DATE
);

-- =========================================================
-- APPROVAL HISTORY (AUDIT LOG)
-- =========================================================
CREATE TABLE approval_history (
    id SERIAL PRIMARY KEY,

    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,

    action VARCHAR(50) NOT NULL,

    performed_by_code VARCHAR(50),

    comment TEXT,

    created_at TIMESTAMP,

    CONSTRAINT fk_approval_employee
        FOREIGN KEY (performed_by_code)
        REFERENCES employees(employee_code)
);