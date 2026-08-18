# WebGuard — Web Application Vulnerability Assessment Platform

WebGuard is a web-based platform that simplifies web application security assessments through a centralized dashboard. Users submit an authorized target URL, monitor each stage of the assessment workflow, review security findings, and download assessment reports from a single interface.

> **Note:** The in-application interface is titled *Web Security Assessment*. **WebGuard** is used here as the product name for this platform.

---

## Overview

WebGuard provides a structured interface for performing web application vulnerability assessments without requiring users to interact directly with the underlying security assessment engine.

Many security testing tools expose low-level controls and technical output that can be difficult to follow. WebGuard addresses this by wrapping the assessment process in a guided workflow with clear progress indicators, organized findings, and downloadable reports.

**Intended users:**

- Developers and students learning web application security
- Teams running authorized assessments in development or test environments
- Reviewers evaluating security assessment workflows in a proof-of-concept setting

**What you can do with WebGuard:**

- Register an account and sign in to a protected assessment dashboard
- Submit a target web application URL for assessment
- Monitor assessment progress through each workflow stage
- Configure active testing duration and stop an in-progress active assessment when needed
- Review a severity summary, top findings, and detailed finding information
- Download HTML and JSON assessment reports

WebGuard is a functional proof of concept. It does not provide enterprise-grade multi-tenant operations, cloud deployment, or AI-driven analysis.

---

## Key Features

- **User registration and login** — Django-based account creation and authentication
- **Authenticated assessment dashboard** — Assessment features require a signed-in user
- **Target URL submission** — HTTP/HTTPS URL validation before an assessment starts
- **Assessment engine connectivity check** — Dashboard verifies the backend assessment engine is reachable before starting
- **Target accessibility verification** — Confirms the target responds before discovery begins
- **Website discovery** — Crawls the target to identify application pages and resources
- **Passive security analysis** — Reviews discovered traffic for security issues without active probing
- **Active vulnerability assessment** — Configurable-duration active security testing against the target
- **Assessment progress monitoring** — Stage indicator, status messages, and progress bars with live updates
- **Configurable assessment duration** — Active testing limits of 5, 10, 15, or 30 minutes
- **Stop active assessment** — User-initiated stop with confirmation during active testing
- **Security findings summary** — Counts grouped by severity (Critical, High, Medium, Low, Informational)
- **Top findings** — Up to five prioritized findings displayed as summary cards
- **Detailed findings view** — Searchable table with per-finding detail panel (description, solution, references)
- **Risk and confidence presentation** — Findings labeled by severity and confidence level
- **HTML report generation** — Downloadable full assessment report
- **JSON report generation** — Machine-readable findings export
- **Modern responsive dashboard** — Dark-themed SOC-style UI built with Bootstrap 5.3

---

## Assessment Workflow

```
User Login
    → Target URL
    → Target Verification
    → Website Discovery
    → Passive Analysis
    → Active Security Assessment
    → Findings Analysis
    → Reports
```

| Stage | Description |
|-------|-------------|
| **User Login** | User authenticates before accessing the assessment dashboard. |
| **Target URL** | User enters the authorized web application URL to assess. |
| **Target Verification** | WebGuard confirms the target is reachable via the assessment engine. |
| **Website Discovery** | The engine crawls the application to map pages and endpoints. |
| **Passive Analysis** | Traffic from discovery is analyzed for security issues without sending attack payloads. |
| **Active Security Assessment** | User selects a duration (5–30 minutes); the engine performs active vulnerability testing. The user may stop the active phase early if needed. |
| **Findings Analysis** | Discovered issues are collected, normalized, and prioritized for display. |
| **Reports** | User reviews results and downloads HTML or JSON reports. |

Only one assessment runs at a time. Assessment state is held in memory for the current session and is not persisted to the database.

---

## Technology Stack

### Backend

- **Python**
- **Django 6.1** — Web application framework, routing, authentication, and API layer
- **requests** — HTTP communication with the assessment engine
- **python-dotenv** — Environment-based configuration

### Frontend

- **HTML** — Server-rendered Django templates
- **CSS** — Custom dashboard styling
- **JavaScript** — Assessment dashboard interactivity and status polling
- **Bootstrap 5.3** — Layout and UI components (CDN)
- **Bootstrap Icons** — Iconography (CDN)

### Database

- **SQLite** — Persistent storage for Django user accounts and authentication data

Assessment results and workflow state are managed in application memory during the current session, not in the database.

### Security Assessment

- **Web Application Vulnerability Assessment Engine** — External engine integrated server-side by the Django application; users interact only through WebGuard

### Configuration

- **Environment variables / `.env`** — Sensitive settings such as the Django secret key, assessment engine host/port, API credentials, and report output directory

---

## Architecture

WebGuard is a monolithic Django application. The browser communicates exclusively with Django; Django orchestrates the assessment workflow and communicates with the external assessment engine on the server side.

```
Browser
    │
    ▼
Django Application  ──────────►  SQLite (user accounts)
    │
    ▼
Vulnerability Assessment Engine
    │
    ▼
Target Web Application
```

**Component responsibilities:**

- **Browser / Frontend** — Landing page, login/signup, assessment dashboard, progress display, findings review, and report downloads
- **Django Web/API Layer** — Authentication, input validation, workflow orchestration, findings normalization, and report generation requests
- **Assessment Engine** — Target verification, discovery, passive analysis, active testing, and raw finding collection
- **SQLite Database** — User account persistence only

Assessment engine credentials and connection details remain server-side and are never exposed to the browser.

---

## Security

WebGuard includes several application-level security controls appropriate for a proof of concept:

- **User authentication** — Signup, login, and logout using Django's built-in auth system
- **Django password hashing** — Passwords stored using Django's default hashing mechanisms
- **Session-based authentication** — Protected pages and API endpoints require an authenticated session
- **Protected assessment pages and APIs** — Dashboard and all assessment API routes use login requirements
- **CSRF protection** — Django CSRF middleware enabled; forms and API requests include CSRF tokens
- **Environment-based configuration** — Sensitive credentials loaded from environment variables / `.env`, not hard-coded for engine access
- **Authorized-target usage** — Workflow designed for explicitly authorized targets only

WebGuard is a development and educational proof of concept. It should not be treated as a hardened, production-ready security platform.

---

## Benefits

- **Centralized assessment workflow** — One dashboard covers the full process from target submission to reporting
- **Easier security testing process** — Guided stages reduce the need to manage scanning steps manually
- **Clear progress visibility** — Stage pipeline, status messages, and progress bars show where an assessment stands
- **Easier interpretation of findings** — Severity summaries, prioritized top findings, and a detailed findings table
- **Structured reporting** — HTML for human review and JSON for tooling or archival
- **Reduced direct engine interaction** — Users work through WebGuard instead of raw scanning interfaces
- **Simple dashboard experience** — Modern, responsive UI suitable for demonstrations and learning
- **Extensible foundation** — Architecture supports future enhancements such as persistent history or additional engines

WebGuard supports early-stage vulnerability identification and security learning. It does not replace professional penetration testing or comprehensive security audits.

---

## Intended Use

WebGuard is designed for:

- **Authorized web application security assessments**
- **Development and testing environments**
- **Security learning and coursework**
- **Security assessment demonstrations**
- **Early-stage vulnerability identification**

**Only assess applications you own or have explicit written authorization to test.** Unauthorized scanning may violate laws and policies.

---

## Project Status

WebGuard is a **functional proof of concept**. The current version demonstrates:

- End-to-end assessment workflow (verification through reporting)
- User authentication (registration, login, protected dashboard)
- Real-time assessment monitoring with stage and progress tracking
- Findings presentation (summary, top findings, detailed view)
- HTML and JSON report generation
- Modern dashboard user interface

This is not a production-ready enterprise security platform. Assessment history, multi-user result isolation, and persistent scan storage are not implemented in the current version.

---

## Future Enhancements

Possible directions for future development:

- Additional vulnerability assessment engines
- Assessment history and persistent results storage
- More advanced reporting and export formats
- Role-based access control
- Multi-user support with per-user assessment records
- Additional security checks and workflow options
- Cloud deployment and production hardening

These items represent potential future work, not current capabilities.

---

## Disclaimer

> WebGuard is intended for authorized security testing and educational purposes. Users should only assess web applications and systems for which they have explicit permission to perform security testing.
