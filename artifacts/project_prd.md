# Product Requirements Document: In-Sight AI Talent Platform

| Status | **Draft** |
| :--- | :--- |
| **Author** | Product Management |
| **Version** | 1.0 |
| **Last Updated** | October 26, 2025 |

## 1. Executive Summary & Vision
In-Sight is an AI-powered performance evaluation and internal mobility dashboard designed for project managers, hiring managers, and talent specialists. It solves the critical business problem of inefficient and biased internal talent discovery by consolidating fragmented employee data into a single, interactive platform. By leveraging quantified performance metrics and AI-generated conversational insights, In-Sight empowers managers to make faster, fairer, and more data-driven decisions about internal opportunities.

Our vision is to unlock the full potential of every employee by creating a transparent, fair, and data-driven internal mobility ecosystem, transforming how we identify, develop, and deploy our internal talent.

## 2. The Problem
**2.1. Problem Statement:**
Our organization struggles to effectively identify and deploy internal talent for new projects and roles. The current process relies on word-of-mouth, outdated spreadsheets, and subjective manager evaluations. This leads to inefficient talent discovery, a high risk of unconscious bias in decision-making, and high-potential employees being overlooked, ultimately resulting in increased attrition and costly external hiring to fill skill gaps.

**2.2. User Personas & Scenarios:**
- **Persona 1: Priya Patel (The Tactical Project Assembler)**
  - **Scenario:** Priya is tasked with staffing a new, high-priority project, "Project Phoenix," which requires engineers with specific skills in "C++" and "Machine Learning." She spends days sending emails and Slack messages to other managers to find available talent, with no objective way to compare the performance of the candidates suggested to her.

- **Persona 2: David Chen (The Strategic Team Builder)**
  - **Scenario:** David needs to fill a Senior Engineer role on his team and wants to promote from within. He has two potential candidates but struggles to prepare for their performance reviews objectively, as his evaluations are based more on recent memory and personal rapport than on a holistic view of their performance data over the last year.

- **Persona 3: Maria Garcia (The Organizational Process Guardian)**
  - **Scenario:** Maria, a Talent Mobility Specialist, is asked by leadership to report on the company's readiness in "Cloud-Native Technologies." She has no centralized way to gather this data and cannot identify which departments have a surplus of this skill and which have critical gaps, hindering strategic workforce planning.

## 3. Goals & Success Metrics
*How will we measure success? This section defines the specific, measurable outcomes we expect.*

| Goal | Key Performance Indicator (KPI) | Target |
| :--- | :--- | :--- |
| Streamline Internal Talent Discovery | Reduction in Time-to-Staff for internal projects | Decrease by 25% within 6 months of launch |
| Increase Internal Mobility | Increase in the Internal Fill Rate for open roles | Achieve a 15% increase in the first year |
| Drive Platform Adoption & Value | Percentage of target managers actively using the platform weekly | Achieve 70% weekly active usage |
| Improve Manager Confidence | Manager Satisfaction Score (NPS) on hiring decisions | Achieve a Net Promoter Score of +40 |

## 4. Functional Requirements & User Stories
*The core of the PRD. This section details what the product must do, broken down into actionable user stories.*

---
**Epic 1: User & Profile Management**
*Core capabilities for creating, viewing, and managing user and employee profiles.*

*   **Story 1 (US-1):** As a System Administrator, I want to add new Project Manager profiles via a modal form so that I can securely provision access for new managers to the platform.
    *   **Acceptance Criteria:**
        *   When I click the 'Add Manager' button, a modal form appears.
        *   The form must contain fields for Manager Name, Email, and Department.
        *   Upon successful submission, the new manager's profile appears in the manager list.
        *   An error message is displayed if the email format is invalid or already exists.
*   **Story 2 (US-2):** As a Project Manager, I want to add a new employee profile using a modal form so that I can quickly populate the dashboard with my team members' data.
    *   **Acceptance Criteria:**
        *   Given I am on the main dashboard, when I click the 'Add Employee' button, a modal form is displayed.
        *   The form includes fields for Name, Title, Skills, and initial performance metrics (e.g., Quality Score, Velocity Rating).
        *   After submitting the form, the new employee appears in the employee list column.
        *   The system validates that required fields are not empty before submission.
*   **Story 3 (US-3):** As a Project Manager, I want to view a comprehensive employee profile in a dedicated panel so that I can assess their skills, experience, and performance history in one place.
    *   **Acceptance Criteria:**
        *   When I click on an employee's name in the list, their full profile loads in the 'Profile View' column.
        *   The profile view must display sections for Skills, Experience, Education, and Quantified Performance Metrics.
        *   The skills section lists each skill with a corresponding proficiency level (e.g., Proficient, Expert).
        *   The performance metrics section displays data for 'Projects Delivered', 'Quality Scores', and 'Velocity Ratings'.
*   **Story 4 (US-11):** As a Talent Mobility Specialist, I want to generate a realistic, synthetic employee profile with one click so that I can demo the platform's features without using real employee data.
    *   **Acceptance Criteria:**
        *   There is a 'Generate Demo Profile' button available in the employee management section.
        *   When clicked, a new, fully populated employee profile is created using realistic but fake data.
        *   The generated profile includes a name, title, skills, and plausible performance metrics.
        *   All synthetically generated profiles are clearly marked as 'Demo Data'.

---
**Epic 2: Talent Discovery & Evaluation**
*Features that enable managers to find, compare, and organize candidates.*

*   **Story 5 (US-4):** As a Project Manager, I want to filter the employee list by specific skills and performance scores so that I can efficiently create a shortlist of qualified candidates for a new project.
    *   **Acceptance Criteria:**
        *   The employee list panel contains filter controls for skills and performance metrics.
        *   When I select a skill (e.g., 'Python'), the list updates in real-time to show only employees with that skill.
        *   When I set a range for 'Quality Score' (e.g., >95%), the list updates to show only employees meeting that criterion.
        *   I can apply multiple filters simultaneously to narrow down the results.
*   **Story 6 (US-5):** As a Hiring Manager, I want to hover over a performance metric to see a detailed tooltip so that I can understand the context and data source behind the number.
    *   **Acceptance Criteria:**
        *   Given an employee profile is displayed, when I hover my cursor over the 'Velocity Rating' metric, a tooltip appears.
        *   The tooltip displays the definition of the metric and the date range it covers.
        *   The tooltip for 'Projects Delivered' shows a list of the last 3 project names.
        *   The tooltip disappears when the cursor is moved away from the metric.
*   **Story 7 (US-6):** As a Hiring Manager, I want to select and view up to three employee profiles side-by-side so that I can directly compare their qualifications for an internal role.
    *   **Acceptance Criteria:**
        *   I can select multiple employees from the list using checkboxes.
        *   When I click the 'Compare' button, a new view opens showing the selected profiles in adjacent columns.
        *   Each column in the comparison view contains a summarized version of the employee's profile, highlighting key skills and metrics.
        *   The system prevents me from selecting more than three employees for comparison at one time.
*   **Story 8 (US-12):** As a Project Manager, I want to create and manage named shortlists of employees so that I can organize candidates for different projects or roles.
    *   **Acceptance Criteria:**
        *   On each employee's profile, there is an 'Add to Shortlist' button.
        *   I can create a new shortlist or add the employee to an existing one.
        *   A dedicated 'Shortlists' panel shows all my created lists and the candidates within each.
        *   I can remove an employee from a shortlist at any time.

---
**Epic 3: AI-Powered Evaluation**
*AI-driven features for generating objective, data-driven conversational insights.*

*   **Story 9 (US-8):** As a Hiring Manager, I want to initiate an AI-generated conversation simulation about an employee so that I can prepare for a data-driven and objective performance review.
    *   **Acceptance Criteria:**
        *   Given an employee profile is selected, a 'Start AI Conversation' button is visible.
        *   When I click the button, the AI conversation panel populates with an initial, context-aware prompt based on the employee's data.
        *   The AI's response analyzes the employee's strengths and potential growth areas based on their profile metrics.
        *   The conversation is presented in a chat-like interface.
*   **Story 10 (US-9):** As a Hiring Manager, I want to inject my own comments into the AI conversation log so that I can add crucial context or team lead feedback to the evaluation record.
    *   **Acceptance Criteria:**
        *   Within the AI conversation panel, there is an 'Inject Comment' button.
        *   When clicked, a text input field appears allowing me to type a manual entry.
        *   My submitted comment appears in the conversation log, clearly distinguished from AI-generated text.
        *   The AI can reference my injected comment in subsequent responses if prompted.
*   **Story 11 (US-10):** As a Project Manager, I want to continue the AI conversation with follow-up questions so that I can explore specific aspects of an employee's performance in greater detail.
    *   **Acceptance Criteria:**
        *   The AI conversation interface includes a text input field for me to type my own questions.
        *   After I submit a question, the AI provides a relevant response based on the conversation history and the employee's profile data.
        *   The entire conversation history remains visible in the panel.
        *   The AI can handle questions like 'Tell me more about their performance on Project X'.

---
**Epic 4: Workspace & Analytics**
*Features related to user interface customization and high-level data visualization.*

*   **Story 12 (US-7):** As a Project Manager, I want to resize and reorder the main dashboard columns so that I can create a personalized workspace that suits my evaluation workflow.
    *   **Acceptance Criteria:**
        *   I can click and drag the border between columns to resize them.
        *   I can click and drag a column header to a new position to reorder the layout.
        *   The dashboard layout changes are automatically saved to my user preferences.
        *   When I log in again, my customized column layout is restored.
*   **Story 13 (US-13):** As a Talent Mobility Specialist, I want to view a team skills matrix dashboard so that I can identify skill gaps and strengths across the organization.
    *   **Acceptance Criteria:**
        *   A 'Team Analytics' view is accessible from the main navigation.
        *   The view displays a heat map showing skills on one axis and employees/teams on the other.
        *   The matrix is color-coded to represent proficiency levels.
        *   I can filter the matrix by department or team to analyze specific groups.

---

## 5. Non-Functional Requirements (NFRs)
- **Performance:**
    - The core dashboard and profile pages must load in under 3 seconds.
    - Filtering and searching the employee list must update the UI in under 500ms.
    - AI conversation responses should be generated and displayed in under 5 seconds.
- **Security:**
    - All employee data must be encrypted in transit (TLS 1.2+) and at rest (AES-256).
    - The system must enforce strict Role-Based Access Control (RBAC) to ensure managers can only view data for employees within their designated scope.
    - The platform must comply with internal data governance policies and external regulations (e.g., GDPR, CCPA).
- **Accessibility:** The user interface must be compliant with Web Content Accessibility Guidelines (WCAG) 2.1 AA standards.
- **Scalability:** The system must be architected to support up to 1,000 concurrent users and a database of 10,000+ employee profiles without performance degradation.

## 6. Release Plan & Milestones
- **Version 1.0 (MVP):** Target Q1 2024 - Core discovery and evaluation workflow.
  - **Scope:** User authentication; Manager & Employee profile creation/viewing (US-1, US-2, US-3); Advanced filtering (US-4); Core AI conversation simulator (US-8, US-10); Candidate shortlisting (US-12); Customizable layout (US-7).
- **Version 1.1:** Target Q2 2024 - Enhanced evaluation and analytics.
  - **Scope:** Side-by-side profile comparison (US-6); Interactive tooltips (US-5); Comment injection in AI conversations (US-9); Team skills matrix (US-13); AI-assisted demo profile generation (US-11).
- **Version 2.0:** Target Q4 2024 - Enterprise integration and automation.
  - **Scope:** HRIS and Project Management tool integrations; AI-powered candidate recommendations; Advanced reporting dashboards.

## 7. Out of Scope & Future Considerations
**7.1. Out of Scope for V1.0:**
- Direct, real-time integration with HRIS or project management systems (initial data population will be via CSV import).
- A native mobile application (the web application will be mobile-responsive).
- AI-powered candidate recommendations and predictive performance trend analysis.
- Advanced administrative reporting on platform usage and internal mobility KPIs.

**7.2. Future Work:**
- Integration with the corporate Learning Management System (LMS) to recommend training based on identified skill gaps.
- AI-powered proactive talent alerts for managers when a team member becomes a good fit for an open internal role.
- Workflow for employees to view and update parts of their own profiles to ensure data accuracy and engagement.

## 8. Appendix & Open Questions
- **Open Question:** What is the definitive source of truth for performance metrics (e.g., Quality Score, Velocity Rating)? Which systems will we need to integrate with in V2.0 to automate this data ingestion?
- **Open Question:** What are the specific data privacy and governance rules we must adhere to regarding employee data visibility across different departments and management levels?
- **Dependency:** The final UI/UX design mockups for the multi-column dashboard and modal forms are required from the Design team by EOW.
- **Dependency:** Access to a sandboxed Large Language Model (LLM) API environment is required for the engineering team to begin prototyping the AI conversation feature.