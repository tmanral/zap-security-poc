# Web Security Assessment POC — Architecture

## 1. Architecture Overview

Build the application as a simple monolithic Django application.

The application has three logical layers:

```text
Browser / Frontend
      |
      v
Django Web/API Layer
      |
      v
ZAP Service Layer
      |
      v
OWASP ZAP API
      |
      v
Local OWASP ZAP Instance
```

- The frontend must communicate only with Django.
- Django must be the only component that communicates with the ZAP API.
- The ZAP API key and ZAP configuration must remain server-side.

## 2. Main Application Components

The application should contain these logical components:

### Frontend

Responsible for:

- Landing page
- Assessment dashboard
- Target URL input
- Active Scan duration selection
- Assessment progress display
- Stop Active Scan control
- Assessment results
- Top findings
- Alert summary
- Report download controls

The frontend should not contain ZAP API calls or ZAP credentials.

### Django Web/API Layer

Responsible for:

- Handling browser requests
- Validating user input
- Starting assessments
- Returning assessment state/progress
- Handling user actions such as stopping a scan
- Returning findings and summaries
- Initiating report generation
- Returning appropriate user-friendly errors

### ZAP Service Layer

Create a dedicated service/client layer responsible for all communication with OWASP ZAP.

It should:

- Build ZAP API requests
- Send requests to ZAP
- Parse ZAP responses
- Handle ZAP API errors
- Provide clean methods to the Django application
- Keep ZAP-specific implementation details outside views

Django views should not contain raw ZAP API URLs throughout the application.

## 3. Suggested Django Structure

Use a clean structure similar to:

```text
project/
│
├── manage.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── assessment/
│   ├── views.py
│   ├── urls.py
│   ├── services/
│   │   └── zap_client.py
│   └── ...
│
├── templates/
│   ├── landing.html
│   └── assessment.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
└── docs/
```

The exact structure may be adjusted if there is a simpler Django-native approach, but responsibilities must remain clearly separated.

Do not introduce unnecessary Django applications.

## 4. ZAP Client / Service

All ZAP communication should be centralized in a dedicated service.

Conceptually:

```text
Django View
      |
      v
Assessment Service
      |
      v
ZAP Client
      |
      v
ZAP API
```

The ZAP client should expose application-friendly methods such as:

- `verify_target()`
- `start_spider()`
- `get_spider_status()`
- `get_spider_results()`
- `get_passive_scan_status()`
- `set_active_scan_duration()`
- `start_active_scan()`
- `get_active_scan_status()`
- `stop_active_scan()`
- `get_alerts()`
- `get_alert_summary()`
- `get_report_templates()`
- `generate_report()`

The rest of the application should not need to know the exact ZAP API URL structure.

## 5. Configuration

ZAP connection settings must be stored in backend configuration.

Example configuration:

```text
ZAP_HOST=localhost
ZAP_PORT=8081
ZAP_API_KEY=<server-side-api-key>
ZAP_REPORT_DIR=L:\Pentest\zap-reports
```

Do not hard-code the API key in Python source code.

Use environment variables or a local configuration mechanism appropriate for the POC.

The following values must never be supplied by the browser:

- ZAP host
- ZAP port
- ZAP API key
- Report directory

## 6. Application-Level Assessment State

No application database is required.

Maintain the current assessment state in memory.

The application should have one central assessment state representation rather than scattering state across multiple views.

Conceptually:

```text
AssessmentState
    |
    ├── application_scan_id
    ├── target_url
    ├── status
    ├── current_stage
    |
    ├── spider_scan_id
    ├── spider_progress
    ├── discovered_url_count
    |
    ├── passive_records_remaining
    |
    ├── active_scan_id
    ├── active_scan_progress
    ├── active_scan_duration
    |
    ├── alert_summary
    ├── findings
    |
    ├── report_paths
    └── scan_completion
```

The application-level scan ID is the primary identifier for the assessment.

Example: `APP-1001`

ZAP's Spider and Active Scan IDs are stored as child values:

- Application Scan ID: `APP-1001`
- Spider Scan ID: `0`
- Active Scan ID: `0`

Do not treat a ZAP scan ID as the application's scan ID.

## 7. Assessment State Machine

The application should manage the workflow using explicit states.

Suggested states:

```text
IDLE
  |
  v
STARTING
  |
  v
VERIFYING_TARGET
  |
  v
DISCOVERING
  |
  v
PASSIVE_SCANNING
  |
  v
ACTIVE_SCANNING
  |
  +-------------------+
  |                    |
  v                    v
COMPLETED           STOPPED
  |                    |
  |                    v
  |                 PARTIAL
  |
  v
RESULTS
  |
  v
REPORT_READY
```

Failure and timeout states should be handled separately:

- `FAILED`
- `TIMEOUT`

A manually stopped or timed-out Active Scan must not be reported as a fully completed assessment.

## 8. Assessment Workflow Orchestration

The backend should control the complete workflow.

The browser should not be responsible for deciding which ZAP API to call next.

The workflow should be:

```text
User submits target
      |
      v
Verify target
      |
      v
Start Spider
      |
      v
Poll Spider status
      |
      v
Spider complete
      |
      v
Retrieve Spider results
      |
      v
Poll Passive Scanner
      |
      v
Passive queue empty
      |
      v
Configure Active Scan duration
      |
      v
Start Active Scan
      |
      v
Poll Active Scan status
      |
      +---- User Stop -----> STOPPED
      |
      +---- Timeout -------> TIMEOUT
      |
      +---- 100% ----------> COMPLETED
      |
      v
Retrieve Alerts
      |
      v
Retrieve Alert Summary
      |
      v
Display Results
      |
      v
Generate Report when requested
```

## 9. Polling

Long-running ZAP operations should be monitored through polling.

Recommended POC polling interval: **3 seconds**

Use polling for:

- Spider status
- Passive scanner status
- Active Scan status

The frontend should receive the current application state from Django rather than directly polling ZAP.

Example:

```text
Browser
   |
   | GET assessment status
   v
Django
   |
   v
Current Assessment State
```

The backend is responsible for communicating with ZAP.

Avoid unnecessary one-second polling.

## 10. Active Scan Control

The user should only control the maximum Active Scan duration through predefined choices:

- 5 minutes
- 10 minutes
- 15 minutes
- 30 minutes

Do not expose an unlimited/maximum option in the initial POC.

The selected value is sent to Django. Django configures ZAP and then starts the Active Scan.

The user may manually stop the Active Scan while it is running.

The Active Scan ID must come from the backend-maintained assessment state.

The user must never provide a ZAP scan ID.

## 11. Results Processing

After Active Scan completion, timeout, or manual stop:

1. Retrieve alerts for the target.
2. Retrieve the target-specific alert summary.
3. Process the results in Django.
4. Store the current results in the in-memory assessment state.
5. Return a simplified response to the frontend.

Do not expose raw ZAP responses directly to the frontend unless necessary.

The backend should transform ZAP data into application-friendly structures.

Example:

```json
{
  "status": "COMPLETED",
  "target": "https://example.com",
  "summary": {
    "high": 2,
    "medium": 5,
    "low": 8,
    "informational": 12
  },
  "top_findings": []
}
```

## 12. Finding Prioritization

The application should display the top five findings.

Prioritize findings approximately as:

1. High
2. Medium
3. Low
4. Informational

Within the same risk level, higher-confidence findings should be prioritized.

The backend should perform this prioritization rather than relying on the order returned by ZAP.

## 13. Report Generation

Report generation should remain controlled by Django.

Supported POC reports:

- HTML
- JSON

Use fixed ZAP templates:

- HTML → `traditional-html`
- JSON → `traditional-json`

The report directory must be configured server-side:

```text
L:\Pentest\zap-reports
```

The user must not be allowed to specify:

- Report directory
- Report filename
- ZAP template name

Generate safe filenames using the application's assessment ID.

Example:

- `APP-1001.html`
- `APP-1001.json`

## 14. Error Handling

The application should handle ZAP and workflow errors gracefully.

Examples include:

- ZAP is not running
- ZAP API is unavailable
- Invalid target URL
- Target cannot be reached
- Spider fails
- Passive scanner does not complete
- Active Scan fails
- Active Scan times out
- Active Scan is manually stopped
- Alert retrieval fails
- Report generation fails
- Report directory is unavailable

The frontend should receive user-friendly error messages.

Do not expose ZAP API keys, internal exceptions, stack traces, or sensitive implementation details to users.

Detailed technical errors may be logged server-side for debugging.

## 15. Single Assessment Constraint

The POC supports only one active assessment at a time.

If an assessment is already running and the user attempts to start another assessment, the application should prevent the second assessment from starting.

Display an appropriate message such as:

> An assessment is already in progress. Please wait for it to complete or stop the current assessment.

Do not implement multi-user or concurrent scan management.

## 16. Security Boundaries

The following rules are mandatory:

1. The ZAP API key must remain server-side.
2. The browser must never call ZAP directly.
3. ZAP scan IDs must remain server-side.
4. Report directory configuration must remain server-side.
5. ZAP API URLs must remain server-side.
6. User-provided target URLs must be validated.
7. User input must not be directly concatenated into shell commands.
8. User input must not be used to construct arbitrary filesystem paths.
9. Report filenames must be generated by the application.
10. Only authorized security testing should be performed.

## 17. POC Simplicity Rules

Keep the implementation simple.

Do not introduce:

- Microservices
- Redis
- Celery
- Message queues
- PostgreSQL
- Docker
- Kubernetes
- Cloud services
- External authentication
- Complex caching
- Distributed processing

...unless a later requirement explicitly requires them.

Prefer Django's built-in capabilities and simple Python services.

The architecture should be easy for a developer/student to understand and modify.
