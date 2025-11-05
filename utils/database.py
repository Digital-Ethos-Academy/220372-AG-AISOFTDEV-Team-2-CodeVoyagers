import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'performance.db')

PROJECT_MANAGER_SEED = [
    {
        "name": "Sarah Johnson", "role": "Senior Project Manager", "department": "Platform Engineering",
        "email": "sarah.johnson@metatech.com", "experience_years": 10, "focus_area": "Scalability",
        "active_project": "Real-Time Event Stream Platform",
        "project_summary": "Building low-latency ingestion and processing pipeline to support analytics and alerting for 40+ internal services.",
        "required_skills": ["React", "Node.js", "Kafka", "Python", "Kubernetes"]
    },
    {
        "name": "Michael Chen", "role": "Technical Project Manager", "department": "Data Science",
        "email": "michael.chen@quantumdynamics.com", "experience_years": 7, "focus_area": "Analytics",
        "active_project": "Predictive Maintenance ML Suite",
        "project_summary": "Coordinating cross-functional effort to deploy anomaly detection models for manufacturing sensor data.",
        "required_skills": ["Python", "Machine Learning", "SQL", "TensorFlow", "API Design"]
    },
    {
        "name": "Emma Rodriguez", "role": "Program Manager", "department": "AI Initiatives",
        "email": "emma.rodriguez@neurallink.com", "experience_years": 9, "focus_area": "Innovation",
        "active_project": "Generative Design Assistant",
        "project_summary": "Leading initiative to prototype AI-driven UI design suggestion tool integrated into internal workflow.",
        "required_skills": ["Figma", "TypeScript", "LLM Prompting", "UX", "Microservices"]
    }
]

EMPLOYEE_SEED = [
    {"name": "Alex Rivera", "title": "Full Stack Developer", "experience_years": 5, "education": "BS Computer Science - Stanford University", "location": "San Francisco, CA", "skills": ["React", "Node.js", "Python", "AWS", "Docker"], "metrics": {"Projects Delivered": "24", "Quality Score": "92/100", "Collaboration": "4.7/5", "Velocity": "21 story points/sprint"}, "summary": "Reliable full-stack engineer consistently delivering scalable features with strong code quality."},
    {"name": "Jordan Kim", "title": "Data Scientist", "experience_years": 3, "education": "MS Data Science - MIT", "location": "Boston, MA", "skills": ["Machine Learning", "Python", "SQL", "Tableau", "TensorFlow"], "metrics": {"Models Deployed": "11", "Impact Uplift": "+18%", "Research Publications": "2", "Velocity": "15 story points/sprint"}, "summary": "Data scientist optimizing predictive models and translating insights into business impact."}
]

SCHEMA_STATEMENTS = [
    "CREATE TABLE IF NOT EXISTS project_managers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, role TEXT, department TEXT, email TEXT, experience_years INTEGER, focus_area TEXT, active_project TEXT, project_summary TEXT, required_skills TEXT)",
    "CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, title TEXT, experience_years INTEGER, education TEXT, location TEXT, skills TEXT, metrics TEXT, summary TEXT)"
]

def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force: bool = False) -> None:
    conn = get_db()
    cur = conn.cursor()
    if force:
        cur.execute("DROP TABLE IF EXISTS project_managers")
        cur.execute("DROP TABLE IF EXISTS employees")
    for stmt in SCHEMA_STATEMENTS:
        cur.execute(stmt)
    # Ensure new columns exist if table was created previously without them
    cur.execute("PRAGMA table_info(project_managers)")
    existing_cols = {row[1] for row in cur.fetchall()}
    new_cols = {
        'active_project': "ALTER TABLE project_managers ADD COLUMN active_project TEXT",
        'project_summary': "ALTER TABLE project_managers ADD COLUMN project_summary TEXT",
        'required_skills': "ALTER TABLE project_managers ADD COLUMN required_skills TEXT"
    }
    for col, alter_stmt in new_cols.items():
        if col not in existing_cols:
            try:
                cur.execute(alter_stmt)
            except Exception:
                pass
    cur.execute("SELECT COUNT(*) FROM project_managers")
    if cur.fetchone()[0] == 0:
        for pm in PROJECT_MANAGER_SEED:
            cur.execute("INSERT INTO project_managers (name, role, department, email, experience_years, focus_area, active_project, project_summary, required_skills) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (pm['name'], pm['role'], pm['department'], pm['email'], pm['experience_years'], pm['focus_area'], pm.get('active_project'), pm.get('project_summary'), json.dumps(pm.get('required_skills', []))))
    cur.execute("SELECT COUNT(*) FROM employees")
    if cur.fetchone()[0] == 0:
        for e in EMPLOYEE_SEED:
            cur.execute("INSERT INTO employees (name, title, experience_years, education, location, skills, metrics, summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (e['name'], e['title'], e['experience_years'], e['education'], e['location'], json.dumps(e['skills']), json.dumps(e['metrics']), e['summary']))
    conn.commit()
    conn.close()

def serialize_project_manager(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'name': row['name'],
        'role': row['role'],
        'department': row['department'],
        'email': row['email'],
        'experience_years': row['experience_years'],
        'focus_area': row['focus_area'],
        'active_project': row['active_project'] if 'active_project' in row.keys() else None,
        'project_summary': row['project_summary'] if 'project_summary' in row.keys() else None,
        'required_skills': json.loads(row['required_skills']) if 'required_skills' in row.keys() and row['required_skills'] else []
    }

def serialize_employee(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'name': row['name'],
        'title': row['title'],
        'experience_years': row['experience_years'],
        'education': row['education'],
        'location': row['location'],
        'skills': json.loads(row['skills']) if row['skills'] else [],
        'metrics': json.loads(row['metrics']) if row['metrics'] else {},
        'summary': row['summary']
    }

def fetch_project_managers() -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM project_managers ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [serialize_project_manager(r) for r in rows]

def fetch_employees() -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [serialize_employee(r) for r in rows]

def fetch_project_manager(mid: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM project_managers WHERE id=?", (mid,))
    row = cur.fetchone()
    conn.close()
    return serialize_project_manager(row) if row else None

def fetch_employee(eid: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id=?", (eid,))
    row = cur.fetchone()
    conn.close()
    return serialize_employee(row) if row else None

def insert_project_manager(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    required_skills = data.get('required_skills', [])
    if isinstance(required_skills, str):
        required_skills = [s.strip() for s in required_skills.split(',') if s.strip()]
    cur.execute("INSERT INTO project_managers (name, role, department, email, experience_years, focus_area, active_project, project_summary, required_skills) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (data.get('name'), data.get('role'), data.get('department'), data.get('email'), data.get('experience_years'), data.get('focus_area'), data.get('active_project'), data.get('project_summary'), json.dumps(required_skills)))
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return fetch_project_manager(mid)

def insert_employee(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO employees (name, title, experience_years, education, location, skills, metrics, summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (data.get('name'), data.get('title'), data.get('experience_years'), data.get('education'), data.get('location'), json.dumps(data.get('skills', [])), json.dumps(data.get('metrics', {})), data.get('summary')))
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return fetch_employee(eid)
