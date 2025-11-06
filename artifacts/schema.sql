CREATE TABLE project_managers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    email TEXT NOT NULL UNIQUE,
    experience_years INTEGER NOT NULL,
    focus_area TEXT,
    active_project TEXT,
    project_summary TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE manager_required_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY (manager_id) REFERENCES project_managers(id) ON DELETE CASCADE,
    UNIQUE(manager_id, skill)
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id INTEGER,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    experience_years INTEGER NOT NULL,
    education TEXT,
    location TEXT,
    summary TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (manager_id) REFERENCES project_managers(id) ON DELETE SET NULL,
    CHECK(experience_years >= 0)
);

CREATE TABLE employee_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(employee_id, skill)
);

CREATE TABLE employee_metrics (
    employee_id INTEGER PRIMARY KEY,
    velocity INTEGER NOT NULL,
    quality_score INTEGER NOT NULL,
    projects_delivered INTEGER NOT NULL,
    skill_alignment_score INTEGER NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    CHECK(quality_score BETWEEN 0 AND 100),
    CHECK(skill_alignment_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_project_managers_email ON project_managers(email);
CREATE INDEX idx_employees_manager_id ON employees(manager_id);
CREATE INDEX idx_employee_metrics_skill_alignment ON employee_metrics(skill_alignment_score);
CREATE INDEX idx_manager_required_skills_skill ON manager_required_skills(skill);
CREATE INDEX idx_employee_skills_skill ON employee_skills(skill);