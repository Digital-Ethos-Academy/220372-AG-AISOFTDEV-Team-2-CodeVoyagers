BEGIN;

-- Seed Project Managers
INSERT INTO project_managers (id, name, role, department, email, experience_years, focus_area, active_project, project_summary) VALUES
(1, 'Priya Patel', 'Project Manager', 'Engineering', 'priya.patel@insight.com', 8, 'AI/ML Initiatives', 'Project Phoenix', 'Developing a next-generation recommendation engine.'),
(2, 'David Chen', 'Engineering Manager', 'Platform', 'david.chen@insight.com', 12, 'Core Infrastructure & Team Building', 'Project Chimera', 'Modernizing the core platform services for scalability.'),
(3, 'Maria Garcia', 'Talent Mobility Specialist', 'HR', 'maria.garcia@insight.com', 6, 'Workforce Planning', 'Org Readiness Initiative', 'Assessing and mapping organizational skills for future growth.'),
(4, 'John Smith', 'Senior Project Manager', 'Infrastructure', 'john.smith@insight.com', 15, 'Cloud Migration', 'Project Stratus', 'Migrating legacy on-premise services to a cloud-native architecture.'),
(5, 'Emily White', 'Product Manager', 'Customer Experience', 'emily.white@insight.com', 7, 'Frontend Development', 'Project Horizon', 'Redesigning the customer-facing web application for improved usability.');

-- Seed Manager Required Skills
INSERT INTO manager_required_skills (manager_id, skill) VALUES
(1, 'C++'),
(1, 'Machine Learning'),
(1, 'Python'),
(2, 'Go'),
(2, 'System Design'),
(2, 'Leadership'),
(3, 'Data Analysis'),
(3, 'Workforce Planning'),
(4, 'AWS'),
(4, 'Kubernetes'),
(4, 'Terraform'),
(5, 'React'),
(5, 'UX Design'),
(5, 'Agile Methodology');

-- Seed Employees
INSERT INTO employees (id, manager_id, name, title, experience_years, education, location, summary) VALUES
(101, 1, 'Anjali Sharma', 'Senior ML Engineer', 8, 'M.S. in Computer Science', 'San Francisco, CA', 'Expert in building and deploying large-scale machine learning models. Key contributor to Project Phoenix.'),
(102, 1, 'Ben Carter', 'Software Engineer', 4, 'B.S. in Software Engineering', 'Austin, TX', 'Proficient C++ developer with a background in performance optimization.'),
(103, 2, 'Carlos Diaz', 'Principal Engineer', 10, 'Ph.D. in Distributed Systems', 'New York, NY', 'Leads architecture for the Platform team, specializing in microservices and high-availability systems.'),
(104, 2, 'Diana Ross', 'Mid-Level Engineer', 5, 'B.S. in Computer Science', 'Remote', 'Go developer focused on API development and containerization for Project Chimera.'),
(105, 4, 'Ethan Hunt', 'DevOps Engineer', 6, 'B.S. in Information Technology', 'Seattle, WA', 'Manages CI/CD pipelines and Kubernetes clusters for the Infrastructure team.'),
(106, 4, 'Fiona Glen', 'Cloud Architect', 9, 'M.S. in Cloud Computing', 'Boston, MA', 'Designs and implements cloud infrastructure solutions on AWS and Azure. Lead on Project Stratus.'),
(107, 5, 'George Lee', 'Frontend Developer', 3, 'Coding Bootcamp Graduate', 'Chicago, IL', 'Specializes in building responsive and accessible user interfaces with React and TypeScript.'),
(108, 5, 'Hannah Kim', 'UX/UI Designer', 5, 'B.A. in Graphic Design', 'San Francisco, CA', 'Leads user research and interface design for Project Horizon, ensuring a seamless user experience.'),
(109, 2, 'Ivan Petrov', 'Senior Software Engineer', 7, 'M.S. in Computer Engineering', 'Remote', 'Experienced Go developer with a strong focus on backend services and database management.'),
(110, 1, 'Jasmine Singh', 'Data Scientist', 4, 'M.S. in Data Science', 'New York, NY', 'Focuses on data analysis and feature engineering for the AI/ML team.');

-- Seed Employee Skills
INSERT INTO employee_skills (employee_id, skill) VALUES
(101, 'C++'), (101, 'Machine Learning'), (101, 'Python'), (101, 'TensorFlow'),
(102, 'C++'), (102, 'Python'), (102, 'SQL'), (102, 'Git'),
(103, 'Go'), (103, 'System Design'), (103, 'PostgreSQL'), (103, 'Microservices'),
(104, 'Go'), (104, 'Docker'), (104, 'gRPC'), (104, 'Kubernetes'),
(105, 'AWS'), (105, 'Kubernetes'), (105, 'CI/CD'), (105, 'Bash Scripting'),
(106, 'AWS'), (106, 'Terraform'), (106, 'Azure'), (106, 'Cloud-Native Technologies'),
(107, 'React'), (107, 'TypeScript'), (107, 'CSS'), (107, 'JavaScript'),
(108, 'Figma'), (108, 'UX Design'), (108, 'User Research'), (108, 'Agile Methodology'),
(109, 'Go'), (109, 'System Design'), (109, 'SQL'), (109, 'Docker'),
(110, 'Python'), (110, 'SQL'), (110, 'Data Analysis'), (110, 'Pandas');

-- Seed Employee Metrics
INSERT INTO employee_metrics (employee_id, velocity, quality_score, projects_delivered, skill_alignment_score) VALUES
(101, 85, 98, 5, 95),
(102, 70, 95, 8, 88),
(103, 90, 99, 4, 97),
(104, 75, 92, 6, 91),
(105, 88, 96, 12, 94),
(106, 82, 98, 3, 99),
(107, 95, 90, 10, 85),
(108, 80, 97, 7, 96),
(109, 85, 94, 9, 93),
(110, 78, 93, 11, 89);

COMMIT;