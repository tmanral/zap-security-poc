# Web Security Assessment POC — Project Overview

## 1. Project Purpose

Build a functional Proof of Concept (POC) web application that provides a simple interface for performing an authorized web application security assessment using a locally running OWASP ZAP instance.

The application will act as an orchestration layer between the user and OWASP ZAP. Users should not interact directly with the ZAP API.

The POC should demonstrate the complete assessment workflow:

**Target URL → Target Verification → Spider → Passive Scanning → Active Scanning → Alerts → Assessment Summary → Report Generation**

---

## 2. Target User

The application is intended for a cybersecurity student/security professional who wants to initiate and observe a basic web application security assessment.

No user authentication or login functionality is required.

Only one user will use the application at a time.

---

## 3. Technology

### Backend

- Python
- Django
- Monolithic Django application

### Security Scanner

- OWASP ZAP 2.17
- ZAP is running locally on the same Windows machine
- ZAP API is accessible through `localhost:8081`

### Frontend

- Use a simple frontend approach that works naturally with the Django application.
- Node.js may be used if required by the selected frontend tooling.
- Frontend and backend/API responsibilities should remain logically separated.

### Database

No application database is required for this POC.

ZAP's own session/data storage is sufficient for the current POC.

The application should maintain the current assessment state in memory.

---

## 4. Application Flow

### Landing Page

When the application starts, users see a simple landing page containing:

- Application name
- Brief explanation of the POC
- High-level explanation of what the application does
- **Begin Security Assessment** button

Clicking the button opens the assessment dashboard.

### Assessment Dashboard

The user enters a target URL and starts the assessment.

After the assessment starts, the remaining workflow should be automated by the backend.

The user should not need to manually trigger individual ZAP APIs.

---

## 5. Assessment Workflow

The application should orchestrate the following workflow:

1. Verify that ZAP can access the target.
2. Start Spider / website discovery.
3. Monitor Spider progress.
4. Retrieve discovered URLs.
5. Monitor passive scanner processing.
6. Configure Active Scan time limit.
7. Start Active Scan.
8. Monitor Active Scan progress.
9. Allow the user to stop the Active Scan.
10. Retrieve security alerts.
11. Display alert/risk summary.
12. Display top findings.
13. Generate HTML and JSON reports.

The detailed ZAP API specification is defined separately in:

- `02_ARCHITECTURE.md`
- `03_ZAP_API_SPECIFICATION.md`

---

## 6. User Controls

Keep user controls minimal.

The user should only control:

- Target URL
- Active Scan duration:
  - 5 minutes
  - 10 minutes
  - 15 minutes
  - 30 minutes
- Stop Active Scan
- View findings
- Generate/download HTML report
- Generate/download JSON report

Do **not** expose the following to users:

- ZAP API key
- ZAP host/port
- ZAP scan IDs
- ZAP configuration
- Spider configuration
- Scan policies
- Attack strength
- Alert thresholds
- Report directory
- ZAP API endpoints

These values must remain controlled by the backend/application configuration.

---


## 7. Application Scan State

The application should maintain its own internal assessment identifier and state.

Example:

```text
Application Scan ID
    |
    ├── Target URL
    ├── Current Stage
    ├── Spider Scan ID
    ├── Spider Progress
    ├── Discovered URL Count
    ├── Passive Scan Status
    ├── Active Scan ID
    ├── Active Scan Progress
    ├── Active Scan Duration
    ├── Alert Summary
    ├── Findings
    └── Assessment Status
```

ZAP Spider and Active Scan IDs are implementation details and must not be exposed to the user.

Possible application states include:

```text
STARTING
VERIFYING_TARGET
DISCOVERING
PASSIVE_SCANNING
ACTIVE_SCANNING
COMPLETED
STOPPED
TIMEOUT
FAILED
```

A stopped or timed-out Active Scan must be treated as a partial assessment.

## 8. POC Architecture Principles

Use a simple, maintainable monolithic Django architecture.

- The browser should communicate with Django.
- Django should communicate with ZAP.
- The browser must not communicate directly with the ZAP API.

Architecture:

```text
Browser
   |
   v
Django Application
   |
   v
Django ZAP Service/API Layer
   |
   v
OWASP ZAP
localhost:8081
```

Keep ZAP integration isolated in a dedicated service/client layer rather than placing ZAP API calls directly throughout Django views.

## 9. Scope and Safety

This application is intended only for authorized security testing.

The application should validate the target URL before starting an assessment.

At minimum:

- Validate URL format.
- Require a valid HTTP/HTTPS URL.
- Do not allow an empty target.
- Handle unreachable targets gracefully.

The application should never imply that a completed automated ZAP scan guarantees that a website is secure.

Assessment results should be presented as automated security findings that may require manual validation.

## 10. Reporting

After scanning, users should initially see a lightweight assessment summary rather than immediately receiving the full report.

The summary should include:

- Target URL
- Assessment status
- High-risk findings count
- Medium-risk findings count
- Low-risk findings count
- Informational findings count
- Top 5 findings

Users can then choose:

- View all findings
- Download HTML report
- Download JSON report

Report files should be generated by ZAP.

The report directory is controlled by the backend and must not be user-configurable.

## 11. POC Constraints

The following are intentionally out of scope:

- Login/authentication system
- Multi-user support
- User accounts
- Application database
- Cloud deployment
- Distributed architecture
- Multiple ZAP instances
- Concurrent assessments
- Kubernetes/Docker infrastructure
- Advanced authentication/session handling for target applications
- Advanced scan policy configuration
- Enterprise-grade scheduling
- Background job infrastructure unless technically required
- Production-grade scalability

Only one assessment should be actively processed at a time.

## 12. Development Priority

The development should follow this priority:

1. Correct ZAP integration
2. Correct assessment workflow
3. Reliable state/progress handling
4. Error handling
5. Functional assessment results
6. Report generation
7. UI/UX improvements
8. Animations and visual polish

The application must be fully functional before visual enhancements are implemented.

Do not over-engineer the POC.
