# Web Security Assessment POC — Functional Requirements

## 1. Purpose

Define the functional behavior of the POC web application.

The application must provide a simple user experience while Django controls the complete OWASP ZAP assessment workflow in the backend.

The priority is a reliable and functional assessment workflow rather than advanced UI design.

---

## 2. Landing Page

When the application is opened, display a landing page.

The landing page should contain:

- Application name
- Short description of the security assessment POC
- Brief explanation of the assessment workflow
- **Begin Security Assessment** button

No login or authentication is required.

### Behavior

When the user clicks **Begin Security Assessment**:

```text
Landing Page
      |
      v
Assessment Dashboard
```

## 3. Assessment Dashboard

The dashboard is the primary assessment screen.

Before starting an assessment, display:

- Target URL input field
- Start Assessment button

Example:

```text
Target URL
[ https://www.example.com ]
[ Start Assessment ]
```

**Validation**

The application must:

- Reject an empty URL.
- Validate URL format.
- Accept HTTP and HTTPS URLs.
- Display a clear validation error for invalid URLs.
- Prevent starting another assessment while one is already running.

The target URL must be validated by Django before being sent to ZAP.

## 4. Assessment Initialization

When the user starts an assessment:

1. Validate the target URL.
2. Create an application-level assessment ID.
3. Initialize the assessment state.
4. Set the status to `STARTING`.
5. Begin Stage 2 automatically.

The user should not manually initiate individual ZAP stages.

Example:

```text
APP-1001
Target: https://www.example.com
Status: STARTING
```

### Stage 2 — Target Verification

## 5. Verify Target Access

After the assessment starts, automatically call the ZAP target-access API.

Purpose: verify that ZAP can reach the supplied target.

**Behavior**

If successful:

```text
✓ Target is reachable
```

Automatically continue to Stage 3.

If unsuccessful:

```text
Unable to access the target.
Please verify the URL and try again.
```

Set the assessment state to `FAILED`.

Do not proceed to Spider if target verification fails.

### Stage 3 — Website Discovery

## 6. Start Spider Automatically

After successful target verification, automatically start the ZAP Spider.

The user should not have to click a Spider button.

Display:

```text
Website Discovery
Starting...
```

When the Spider API returns a scan ID, save it internally.

Do not expose the ZAP scan ID to the user.

## 7. Spider Progress

Poll the Spider status automatically.

Recommended polling interval: **3 seconds**

Display the progress to the user.

Example:

```text
Website Discovery
██████████░░░░░░░░░░ 50%
Discovering application pages...
```

When the Spider reaches 100%:

```text
✓ Website discovery completed
```

Automatically retrieve the Spider results.

## 8. Display Spider Results

After Spider completion, retrieve the discovered URLs.

Display a lightweight result such as:

```text
✓ Website discovery completed
Discovered 37 URLs
```

The POC does not need to display every discovered URL on the main progress screen.

Optionally provide a "View Discovered URLs" control if simple to implement.

The discovered URLs should not be manually passed from the frontend to later ZAP stages.

### Stage 4 — Passive Scanning

## 9. Monitor Passive Scanner

After Spider results are retrieved, automatically monitor the ZAP passive scanner.

Poll approximately every 3 seconds.

Display:

```text
Passive Security Analysis
Analyzing discovered traffic...
```

The application should monitor `recordsToScan`.

**When records remain**

Continue polling.

**When records reach zero**

Treat the passive scanner queue as complete for the current workflow and proceed to Stage 5.

Display:

```text
✓ Passive security analysis completed
Preparing active security testing...
```

Do not interpret `recordsToScan = 0` as "zero vulnerabilities."

### Stage 5 — Active Security Testing

## 10. Select Active Scan Duration

Before starting the Active Scan, show the user predefined duration options:

```text
Active Scan Duration
○ 5 minutes
○ 10 minutes
○ 15 minutes
○ 30 minutes
```

Do not expose an unlimited/max-duration option in the initial POC.

The user must select one duration before starting the Active Scan.

## 11. Start Active Scan

After the user selects the duration:

1. Configure the ZAP Active Scan duration.
2. Start the Active Scan automatically.
3. Save the returned ZAP Active Scan ID internally.
4. Begin polling the Active Scan status.

Display:

```text
Active Security Testing
Attack/testing started...
```

The user must not enter or modify the ZAP Active Scan ID.

## 12. Active Scan Progress

Poll Active Scan status approximately every 3 seconds.

Display the current progress.

Example:

```text
Active Security Testing
██████████░░░░░░░░░░ 50%
Testing application for vulnerabilities...
```

When progress reaches 100%:

```text
✓ Active security testing completed
```

Automatically proceed to Stage 6.

## 13. Stop Active Scan

While Active Scan is running, display:

```text
[ Stop Scan ]
```

When clicked:

1. Send the stop request through Django.
2. Use the internally stored Active Scan ID.
3. Update application state to `STOPPED`.
4. Mark the assessment as `PARTIAL`.
5. Stop Active Scan polling.
6. Proceed to Stage 6.

Display:

```text
Active scan stopped.
The following results represent a partial assessment.
```

The user must never provide the ZAP scan ID.

## 14. Active Scan Timeout

If the configured Active Scan duration is reached:

1. Treat the scan as time-limited.
2. Update application state appropriately.
3. Mark the assessment as `PARTIAL`.
4. Proceed to Stage 6 and retrieve available findings.

Display:

```text
Active scan reached the configured time limit.
Available findings will now be analyzed.
```

The results must clearly indicate that the Active Scan was not allowed to complete fully.

### Stage 6 — Security Findings

## 15. Retrieve Alerts

After Active Scan completion, manual stop, or timeout:

Automatically retrieve alerts associated with the target URL.

Do not require user interaction.

The backend should process the raw ZAP alerts into application-friendly finding objects.

Each finding should retain useful information such as:

- Alert name
- Risk
- Confidence
- Affected URL
- Parameter
- Description
- Solution
- Reference

## 16. Retrieve Alert Summary

Automatically retrieve the target-specific alert summary.

Display counts for: High, Medium, Low, Informational.

Example:

```text
Security Assessment Results
HIGH           2
MEDIUM         5
LOW            8
INFORMATIONAL  12
```

Use the target URL as the filter.

Do not display a session-wide summary when a target-specific summary is available.

## 17. Top Five Findings

After retrieving alerts:

1. Process the findings in Django.
2. Prioritize higher-risk findings.
3. Use confidence as a secondary prioritization factor.
4. Select the top five findings.

Suggested priority: High → Medium → Low → Informational

Within the same risk level: High Confidence → Medium Confidence → Low Confidence

Display the top five findings on the assessment results screen.

Example:

```text
Top Findings

1. High — Example Vulnerability
   https://www.example.com/login

2. High — Example Vulnerability
   https://www.example.com/search

3. Medium — Example Vulnerability
   https://www.example.com/account
```

Do not assume that the first five records returned by ZAP are automatically the five most important findings.

## 18. View All Findings

Provide a control:

```text
[ View All Findings ]
```

When selected, display the complete set of retrieved target-specific findings.

The findings should be presented in a readable table or list.

Recommended fields:

| Field | Display |
|---|---|
| Risk | Yes |
| Confidence | Yes |
| Finding | Yes |
| Affected URL | Yes |
| Parameter | Optional |
| Description | On detail view |
| Solution | On detail view |
| Reference | On detail view |

The initial POC does not require advanced filtering or sorting controls.

### Stage 7 — Reporting

## 19. Report Options

After the assessment results are available, display:

```text
[ Download HTML Report ]
[ Download JSON Report ]
```

Do not require the user to select or enter a ZAP template name.

The application should internally map:

- HTML → `traditional-html`
- JSON → `traditional-json`

## 20. Generate HTML Report

When the user selects **Download HTML Report**, Django should:

1. Request HTML report generation from ZAP.
2. Use the configured report directory.
3. Generate a safe application-specific filename.
4. Verify that the report was generated.
5. Return the report to the browser.

Example filename: `APP-1001.html`

The report directory must remain backend-controlled.

Configured POC directory:

```text
L:\Pentest\zap-reports
```

The user must not be able to change the directory or filename.

## 21. Generate JSON Report

When the user selects **Download JSON Report**, Django should:

1. Request JSON report generation from ZAP.
2. Use the configured report directory.
3. Generate a safe application-specific filename.
4. Verify that the report was generated.
5. Return the report to the browser.

Example filename: `APP-1001.json`

## 22. Assessment Progress UI

The application should provide a clear indication of the current stage.

Suggested stages:

1. Target Verification
2. Website Discovery
3. Passive Analysis
4. Active Security Testing
5. Findings Analysis
6. Report Generation

The user should always be able to understand:

- Current stage
- Progress where available
- What the application is currently doing
- Whether the assessment succeeded, failed, stopped, or timed out

Avoid exposing technical ZAP API details to the user.

## 23. Assessment Completion

For a fully completed assessment:

```text
Assessment Status: COMPLETED
Assessment Type: FULL
```

Display:

```text
✓ Security assessment completed
```

For a manually stopped assessment:

```text
Assessment Status: STOPPED
Assessment Type: PARTIAL
```

For a time-limited assessment:

```text
Assessment Status: TIMEOUT
Assessment Type: PARTIAL
```

The results screen must clearly distinguish a full assessment from a partial assessment.

## 24. Error Handling

The application must handle common failures gracefully.

**ZAP unavailable**

```text
OWASP ZAP is unavailable.
Please make sure ZAP is running and try again.
```

**Invalid URL**

```text
Please enter a valid HTTP or HTTPS URL.
```

**Target unreachable**

```text
The target could not be reached.
Please verify the target URL and try again.
```

**Spider failure**

```text
Website discovery could not be completed.
```

**Active Scan failure**

```text
Active security testing could not be completed.
```

**Report generation failure**

```text
The report could not be generated.
Please try again.
```

Do not expose:

- API keys
- Python stack traces
- Internal filesystem paths
- Raw ZAP exceptions
- Internal implementation details

Technical details may be logged server-side.

## 25. Single Assessment Rule

Only one assessment may run at a time.

If an assessment is already running, disable the Start Assessment action.

If necessary, display:

```text
An assessment is already in progress.
Please wait for it to complete or stop the current assessment.
```

No multi-user or concurrent assessment functionality is required.

## 26. Assessment Reset

After an assessment reaches a final state — `COMPLETED`, `STOPPED`, `TIMEOUT`, or `FAILED` — the user should be able to start another assessment.

Starting a new assessment should create a new application-level assessment ID and reset the previous in-memory application state.

Example:

```text
APP-1001 → Completed

New assessment
APP-1002 → Starting
```

Do not reuse the previous application scan ID.

## 27. Frontend and Backend Responsibilities

**Frontend**

The frontend is responsible for:

- Displaying pages
- Collecting target URL
- Collecting Active Scan duration
- Displaying progress
- Displaying status messages
- Providing Stop Scan action
- Displaying findings
- Providing report download controls

**Backend**

The backend is responsible for:

- Input validation
- Assessment state
- Workflow orchestration
- ZAP API communication
- Polling
- Scan ID management
- Error handling
- Alert processing
- Finding prioritization
- Report generation
- Report file handling

The frontend must never directly communicate with ZAP.

## 28. Functional Success Criteria

The POC is considered functionally complete when a user can:

1. Open the application.
2. See the landing page.
3. Navigate to the assessment dashboard.
4. Enter a target URL.
5. Start an assessment.
6. See target verification progress/result.
7. See Spider progress.
8. See discovered URL count.
9. See passive scanning progress/state.
10. Select an Active Scan duration.
11. Start Active Scan.
12. See Active Scan progress.
13. Stop Active Scan if desired.
14. Allow Active Scan to complete if desired.
15. See the security alert summary.
16. See the top five findings.
17. View all available findings.
18. Generate/download an HTML report.
19. Generate/download a JSON report.
20. Start another assessment after the previous assessment reaches a final state.

## 29. Out of Scope for the Functional POC

Do not implement the following unless explicitly requested later:

- Login
- User registration
- User profiles
- Application database
- Scan history
- Multiple users
- Concurrent scans
- Scheduled scans
- Email notifications
- Cloud deployment
- Advanced ZAP configuration
- Custom scan policies
- Custom attack strength
- Authentication against target applications
- Complex target session handling
- Multiple ZAP instances
- Additional security scanners
- Advanced report customization
- Enterprise-scale job processing

The goal is a small, functional, understandable OWASP ZAP assessment POC.
