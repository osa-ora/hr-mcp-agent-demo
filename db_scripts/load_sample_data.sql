-- ==================================================
-- EMPLOYEES
-- ==================================================
INSERT INTO employees (
    employee_code, full_name, sex, birthdate, marital_status,
    nationality, manager_code, created_at, updated_at
) VALUES
('CEO001','Ahmed Hassan','M','1978-01-15','married','Egyptian',NULL,NOW(),NOW()),
('MGR001','Mohamed Mourad','M','1985-03-10','married','Egyptian','CEO001',NOW(),NOW()),
('EMP001','Osama Oransa','M','1990-05-01','single','Egyptian','MGR001',NOW(),NOW()),
('EMP002','Sara Ali','F','1994-08-20','single','Egyptian','MGR001',NOW(),NOW());


-- ==================================================
-- EMPLOYEE CONTACTS
-- ==================================================
INSERT INTO employee_contacts (
    employee_code, contact_type, value, is_primary, created_at
) VALUES
('EMP001','email','osama@example.com',TRUE,NOW()),
('EMP001','phone','+201234567890',TRUE,NOW()),
('EMP002','email','sara@example.com',TRUE,NOW()),
('MGR001','email','mourad@example.com',TRUE,NOW()),
('CEO001','email','ceo@example.com',TRUE,NOW());


-- ==================================================
-- EMPLOYEE EMPLOYMENT
-- ==================================================
INSERT INTO employee_employment (
    employee_code, hire_date, title, department,
    employment_type, employment_status, location
) VALUES
('EMP001','2023-01-01','Software Engineer','Engineering','full-time','active','Cairo'),
('EMP002','2023-06-01','QA Engineer','Engineering','full-time','active','Cairo'),
('MGR001','2020-01-01','Engineering Manager','Engineering','full-time','active','Cairo'),
('CEO001','2015-01-01','CEO','Executive','full-time','active','Cairo');


-- ==================================================
-- EMPLOYEE LEAVE BALANCE
-- ==================================================
INSERT INTO employee_leave_balance (
    employee_code, annual_leave_days, sick_leave_days,
    parental_leave_days, last_updated
) VALUES
('EMP001',30,10,5,NOW()),
('EMP002',25,10,5,NOW()),
('MGR001',40,15,10,NOW()),
('CEO001',50,20,10,NOW());


-- ==================================================
-- LEAVE TYPES
-- ==================================================
INSERT INTO leave_types (
    type_name, description, requires_approval, max_days_per_year
) VALUES
('Annual Leave','Yearly vacation leave',TRUE,30),
('Sick Leave','Medical leave',FALSE,10),
('Parental Leave','Family leave',TRUE,10);


-- ==================================================
-- POLICIES
-- ==================================================
INSERT INTO policies (
    policy_name, category, content, version, effective_date
) VALUES
('Annual Leave Policy','Leave','Employees get annual leave based on seniority.','1.0','2024-01-01'),
('Remote Work Policy','Work','Hybrid work allowed depending on manager approval.','1.0','2024-01-01');


-- ==================================================
-- COMPENSATION
-- ==================================================
INSERT INTO employee_compensation (
    employee_code, base_salary, currency, allowance, effective_from, created_at
) VALUES
('EMP001',3000,'USD',500,'2024-01-01',NOW()),
('EMP002',2800,'USD',400,'2024-01-01',NOW()),
('MGR001',6000,'USD',1000,'2024-01-01',NOW()),
('CEO001',12000,'USD',3000,'2024-01-01',NOW());


-- ==================================================
-- LEAVE REQUESTS
-- ==================================================
INSERT INTO leave_requests (
    employee_code, leave_type_id, start_date, end_date,
    delegate_employee_code, comment, status, created_at
) VALUES
('EMP001',1,'2024-06-10','2024-06-15','EMP002','Family vacation','PENDING',NOW()),
('EMP002',2,'2024-07-01','2024-07-03','EMP001','Medical leave','APPROVED',NOW());