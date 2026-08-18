# OWASP ZAP API Specification

## 1. Purpose

This document defines the OWASP ZAP APIs that the Django application will use for the POC security assessment workflow.

The Django backend is the only component that communicates with ZAP.

The frontend must never call ZAP APIs directly.

---

## 2. ZAP Configuration

ZAP is running locally on the same Windows machine as the Django application.

Default configuration:

```text
ZAP Host: localhost
ZAP Port: 8081
ZAP Base URL: http://localhost:8081
```

The ZAP API key must be stored server-side through application configuration/environment variables.

Example:

```text
ZAP_API_KEY=<server-side-api-key>
```

Do not expose the API key to the frontend.

All API requests should use the configured API key.

## 3. General API Rules

ZAP API requests use the following general structure:

```text
http://localhost:8081/JSON/<component>/<type>/<operation>/
```

Most POC API calls use `GET` with query parameters.

The Django ZAP client should construct and send these requests.

The frontend should never know the actual ZAP API URLs.

### Stage 1 — Begin Security Assessment

There is no ZAP API for this stage.

The user clicks **Begin Security Assessment**.

The Django application creates an internal application-level assessment ID.

Example: `APP-1001`

Initial state:

```text
status = STARTING
currentStage = VERIFYING_TARGET
```

The application-level assessment ID must be used to associate all subsequent ZAP operations and results.

### Stage 2 — Verify ZAP Can Access the Target

**API**

`GET /JSON/core/action/accessUrl/`

**Full API URL**

`http://localhost:8081/JSON/core/action/accessUrl/`

**Parameters**

| Parameter | Source | Required | Description |
|---|---|---|---|
| apikey | Backend configuration | Yes | ZAP API authentication |
| url | User target URL | Yes | Target website/application |
| followRedirects | Backend | Yes | Set to true |

Example:

```text
http://localhost:8081/JSON/core/action/accessUrl/?apikey=YOUR_API_KEY&url=https%3A%2F%2Fwww.xyz.com&followRedirects=true
```

**User Input**

Only: `targetUrl`

Example: `https://www.xyz.com`

**Backend-Controlled Values**

- `apikey`
- `followRedirects=true`

**Expected Response**

```json
{
  "accessUrl": [
    {
      "note": "",
      "rtt": "929",
      "responseBody": "<html>...</html>",
      "cookieParams": "",
      "responseHeader": "HTTP/1.1 200 OK",
      "id": "1",
      "type": "15",
      "timestamp": "1786999325698",
      "tags": []
    }
  ]
}
```

**Data Required for Later Stages**

The response body does not need to be passed manually to later stages.

The application should determine whether the target was accessible.

Optionally save:

- `targetAccessible`
- `httpStatus`
- `responseTime`

If the target cannot be accessed, stop the assessment and display an appropriate error.

### Stage 3 — Spider / Website Discovery

#### Stage 3.1 — Start Spider

**API**

`GET /JSON/spider/action/scan/`

**Full API URL**

`http://localhost:8081/JSON/spider/action/scan/`

**Parameters**

| Parameter | Source | Required | Description |
|---|---|---|---|
| apikey | Backend configuration | Yes | ZAP API authentication |
| url | Assessment target URL | Yes | Target to discover |
| recurse | Backend | Yes | Set to true |

Example:

```text
http://localhost:8081/JSON/spider/action/scan/?apikey=YOUR_API_KEY&url=https%3A%2F%2Fwww.xyz.com&recurse=true
```

**User Input**

None. The target URL comes from the current application assessment.

**Expected Response**

```json
{
  "scan": "0"
}
```

**Required Data to Save**

Save: `spiderScanId = 0`

The Spider scan ID belongs to the ZAP Spider operation. Do not expose it to the user.

#### Stage 3.2 — Check Spider Status

**API**

`GET /JSON/spider/view/status/`

**Full API URL**

`http://localhost:8081/JSON/spider/view/status/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| scanId | Saved spiderScanId | Yes |

Example:

```text
http://localhost:8081/JSON/spider/view/status/?apikey=YOUR_API_KEY&scanId=0
```

**Expected Response**

```json
{
  "status": "57"
}
```

The value represents Spider progress.

**Polling**

The backend should poll approximately every **3 seconds**.

Do not poll every second unless specifically required.

**Workflow**

```text
status < 100
      |
      v
Continue polling

status = 100
      |
      v
Spider completed
```

**Frontend**

The backend should expose the progress to the frontend.

Example:

```text
Website Discovery
████████████░░░░░░░░ 57%
Discovering application pages...
```

The frontend must not directly poll ZAP.

#### Stage 3.3 — Get Spider Results

**API**

`GET /JSON/spider/view/results/`

**Full API URL**

`http://localhost:8081/JSON/spider/view/results/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| scanId | Saved spiderScanId | Yes |

Example:

```text
http://localhost:8081/JSON/spider/view/results/?apikey=YOUR_API_KEY&scanId=0
```

**Expected Response**

```json
{
  "results": [
    "https://www.xyz.com/",
    "https://www.xyz.com/login",
    "https://www.xyz.com/about"
  ]
}
```

**Data to Save**

For the POC, save: `discoveredUrlCount`

Optionally retain: `discoveredUrls[]`

The Spider results do not need to be manually supplied to the Active Scan API. ZAP maintains the discovered application information within its current session.

### Stage 4 — Passive Scanner

#### Stage 4.1 — Check Passive Scanner Status

**API**

`GET /JSON/pscan/view/recordsToScan/`

**Full API URL**

`http://localhost:8081/JSON/pscan/view/recordsToScan/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |

Example:

```text
http://localhost:8081/JSON/pscan/view/recordsToScan/?apikey=YOUR_API_KEY
```

**Expected Response**

```json
{
  "recordsToScan": "0"
}
```

**Interpretation**

`recordsToScan` represents the number of HTTP messages currently waiting to be processed by the passive scanner. It does NOT represent the number of vulnerabilities.

```text
recordsToScan > 0
      |
      v
Continue waiting

recordsToScan = 0
      |
      v
Passive scanner queue is currently empty
```

**Polling**

Poll approximately every **3 seconds**.

**Important**

Passive scanning may continue to receive/process traffic generated by later ZAP operations. Therefore, the application should not assume that passive scanning and active scanning are completely isolated processes.

### Stage 5 — Active Scanner

#### Stage 5.0 — Configure Maximum Active Scan Duration

This stage is optional from a ZAP API perspective but recommended for this POC.

The user selects one of: 5 minutes, 10 minutes, 15 minutes, 30 minutes.

The application should not expose an unlimited option in the initial POC.

**API**

`GET /JSON/ascan/action/setOptionMaxScanDurationInMins/`

**Full API URL**

`http://localhost:8081/JSON/ascan/action/setOptionMaxScanDurationInMins/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| Integer | User-selected duration | Yes |

Example for 10 minutes:

```text
http://localhost:8081/JSON/ascan/action/setOptionMaxScanDurationInMins/?apikey=YOUR_API_KEY&Integer=10
```

**Important**

This API configures the maximum Active Scan duration. It does NOT start the Active Scan. The Active Scan is still started using `ascan/action/scan`.

#### Stage 5.1 — Start Active Scan

**API**

`GET /JSON/ascan/action/scan/`

**Full API URL**

`http://localhost:8081/JSON/ascan/action/scan/`

**Parameters**

| Parameter | Source | Required | Description |
|---|---|---|---|
| apikey | Backend configuration | Yes | ZAP API authentication |
| url | Assessment target URL | Yes | Active Scan starting URL |
| recurse | Backend | Yes | Set to true |

Example:

```text
http://localhost:8081/JSON/ascan/action/scan/?apikey=YOUR_API_KEY&url=https%3A%2F%2Fwww.xyz.com&recurse=true
```

**Expected Response**

```json
{
  "scan": "0"
}
```

**Required Data to Save**

Save: `activeScanId = 0`

The Active Scan ID is different from the Spider scan ID even if both happen to have the same numeric value.

Example:

```text
Application Scan ID: APP-1001
Spider Scan ID: 0
Active Scan ID: 0
```

These are three different identifiers.

#### Stage 5.2 — Check Active Scan Status

**API**

`GET /JSON/ascan/view/status/`

**Full API URL**

`http://localhost:8081/JSON/ascan/view/status/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| scanId | Saved activeScanId | Yes |

Example:

```text
http://localhost:8081/JSON/ascan/view/status/?apikey=YOUR_API_KEY&scanId=0
```

**Expected Response**

```json
{
  "status": "35"
}
```

**Polling**

Poll approximately every **3 seconds**.

**Workflow**

```text
status < 100
      |
      v
Continue polling

status = 100
      |
      v
Active Scan completed
```

The frontend should display the progress.

Example:

```text
Active Security Testing
███████░░░░░░░░░░░ 35%
Testing application for vulnerabilities...
```

#### Stage 5.3 — Stop Active Scan

The user should have a Stop button while Active Scan is running.

**API**

`GET /JSON/ascan/action/stop/`

**Full API URL**

`http://localhost:8081/JSON/ascan/action/stop/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| scanId | Saved activeScanId | Yes |

Example:

```text
http://localhost:8081/JSON/ascan/action/stop/?apikey=YOUR_API_KEY&scanId=0
```

**User Input**

The user only clicks **Stop Scan**. The user must never enter the ZAP scan ID.

**Result**

After stopping:

```text
application status = STOPPED
scan completion = PARTIAL
```

The application may proceed to Stage 6 and retrieve alerts. Alerts discovered before stopping remain available in ZAP.

The report/result UI must clearly indicate that the assessment was partial.

### Stage 6 — Retrieve Alerts

#### Stage 6.1 — Retrieve All Alerts for Target

**API**

`GET /JSON/core/view/alerts/`

**Full API URL**

`http://localhost:8081/JSON/core/view/alerts/`

**Parameters**

| Parameter | Source | Required | Description |
|---|---|---|---|
| apikey | Backend configuration | Yes | ZAP authentication |
| baseurl | Assessment target URL | Yes | Restrict alerts to target |
| start | Backend | Yes | Pagination start |
| count | Backend | Yes | Number of results |

Example:

```text
http://localhost:8081/JSON/core/view/alerts/?apikey=YOUR_API_KEY&baseurl=https%3A%2F%2Fwww.xyz.com&start=0&count=999
```

**Important**

Use `baseurl` to restrict results to the current assessment target. Do not retrieve all alerts from the entire ZAP session unless specifically required.

**Expected Data**

Alerts may contain information such as: `alert`, `risk`, `confidence`, `url`, `param`, `description`, `solution`, `reference`.

**Data to Retain**

For the POC, retain at least: alert name, risk, confidence, affected URL, parameter, description, solution, reference.

The raw alert response may also be retained in memory for report/result processing.

#### Stage 6.2 — Get Alert Summary

**API**

`GET /JSON/core/view/alertsSummary/`

**Full API URL**

`http://localhost:8081/JSON/core/view/alertsSummary/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| baseurl | Assessment target URL | Yes |

Example:

```text
http://localhost:8081/JSON/core/view/alertsSummary/?apikey=YOUR_API_KEY&baseurl=https%3A%2F%2Fwww.xyz.com
```

**Expected Response**

Conceptually:

```json
{
  "alertsSummary": {
    "High": 2,
    "Medium": 5,
    "Low": 8,
    "Informational": 12
  }
}
```

The exact response structure should be handled based on the installed ZAP version.

**Important**

Use `baseurl`. Without `baseurl`, the summary may represent the broader alert state currently held in the ZAP session rather than only the current target.

Do not use a ZAP Spider or Active Scan ID for this API.

#### Stage 6.3 — Top Findings

ZAP alert retrieval should provide the raw findings.

The Django backend should determine the top five findings.

Do not assume that `start=0&count=5` means the five most important vulnerabilities.

Instead:

1. Retrieve target-specific alerts.
2. Sort by risk.
3. Use confidence as a secondary prioritization factor.
4. Select the top five.
5. Return them to the frontend.

Suggested priority: High → Medium → Low → Informational

Within the same risk level: High confidence → Medium confidence → Low confidence

The frontend should display a simplified version of each finding.

### Stage 7 — Report Generation

#### Stage 7.1 — Get Available Report Templates

**API**

`GET /JSON/reports/view/templates/`

**Full API URL**

`http://localhost:8081/JSON/reports/view/templates/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |

Example:

```text
http://localhost:8081/JSON/reports/view/templates/?apikey=YOUR_API_KEY
```

**Example Response**

```json
{
  "templates": [
    "traditional-json",
    "sarif-json",
    "modern",
    "auth-report-json",
    "traditional-md",
    "traditional-pdf",
    "traditional-xml",
    "traditional-html",
    "traditional-html-plus",
    "traditional-json-plus"
  ]
}
```

The exact list may vary depending on the installed ZAP version and add-ons.

**POC Usage**

The user does not need to see every available template.

The application should support only:

- HTML → `traditional-html`
- JSON → `traditional-json`

The template API can be called during application startup or when required and cached.

Do not allow users to enter arbitrary template names.

#### Stage 7.2 — Generate HTML Report

**API**

`GET /JSON/reports/action/generate/`

**Full API URL**

`http://localhost:8081/JSON/reports/action/generate/`

**Parameters**

| Parameter | Source | Required |
|---|---|---|
| apikey | Backend configuration | Yes |
| title | Backend-generated | Yes |
| template | Backend fixed value | Yes |
| sites | Assessment target URL | Yes |
| reportDir | Backend configuration | Yes |
| reportFileName | Backend-generated | Yes |
| display | Backend | Optional |

**POC Values**

```text
template = traditional-html
reportDir = L:\Pentest\zap-reports
display = false
```

Example:

```text
http://localhost:8081/JSON/reports/action/generate/?apikey=YOUR_API_KEY&title=XYZ%20Security%20Assessment&template=traditional-html&sites=https%3A%2F%2Fwww.xyz.com&reportDir=L%3A%5CPentest%5Czap-reports&reportFileName=APP-1001.html&display=false
```

**Report Location**

```text
L:\Pentest\zap-reports\APP-1001.html
```

The user must not control the report directory or filename.

#### Stage 7.3 — Generate JSON Report

**API**

`GET /JSON/reports/action/generate/`

Use the same API as HTML generation.

**POC Values**

```text
template = traditional-json
reportDir = L:\Pentest\zap-reports
display = false
```

Example:

```text
http://localhost:8081/JSON/reports/action/generate/?apikey=YOUR_API_KEY&title=XYZ%20Security%20Assessment&template=traditional-json&sites=https%3A%2F%2Fwww.xyz.com&reportDir=L%3A%5CPentest%5Czap-reports&reportFileName=APP-1001.json&display=false
```

**Report Location**

```text
L:\Pentest\zap-reports\APP-1001.json
```

## 8. Complete API Workflow

The Django application should orchestrate the APIs in this order:

```text
User
  |
  | Target URL
  v
Stage 2: accessUrl
  |
  | Target accessible
  v
Stage 3.1: Start Spider
  |
  | spiderScanId
  v
Stage 3.2: Poll Spider Status
  |
  | 100%
  v
Stage 3.3: Get Spider Results
  |
  v
Stage 4: Poll Passive Scanner
  |
  | recordsToScan = 0
  v
Stage 5.0: Configure Active Scan Duration
  |
  v
Stage 5.1: Start Active Scan
  |
  | activeScanId
  v
Stage 5.2: Poll Active Scan Status
  |
  +------------------------+
  |                        |
  | 100%                   | User Stop / Timeout
  |                        |
  v                        v
COMPLETED                PARTIAL
  |                        |
  +-----------+------------+
              |
              v
        Stage 6.1: Retrieve Alerts
              |
              v
        Stage 6.2: Retrieve Alert Summary
              |
              v
        Display Results
              |
  +-----------+------------+
  |                        |
  v                        v
View Findings         Generate Report
                            |
                    +-------+-------+
                    |               |
                    v               v
                  HTML            JSON
```

## 9. Application-Level State Mapping

The application must maintain its own state independently from ZAP scan IDs.

Example:

```text
Application Scan
-----------------
applicationScanId = APP-1001
targetUrl = https://www.xyz.com
status = ACTIVE_SCANNING

ZAP Spider
-----------
spiderScanId = 0
spiderProgress = 100

Passive Scanner
-----------------
recordsToScan = 0

ZAP Active Scan
-----------------
activeScanId = 0
activeScanProgress = 65

Results
--------
alertSummary = ...
findings = ...

Reports
--------
htmlReportPath = ...
jsonReportPath = ...
```

The application-level assessment ID is the primary identifier.

## 10. Error and Status Handling

The application should not assume every ZAP API request succeeds.

For each ZAP API call:

1. Send the request.
2. Check the HTTP response.
3. Validate the expected JSON structure.
4. Detect ZAP API errors.
5. Update application state.
6. Return a user-friendly status to the frontend.

Examples:

| Condition | Status |
|---|---|
| ZAP unavailable | `ZAP_UNAVAILABLE` |
| Target unreachable | `TARGET_UNREACHABLE` |
| Spider failure | `SPIDER_FAILED` |
| Active Scan stopped | `STOPPED` / `PARTIAL` |
| Active Scan timeout | `TIMEOUT` / `PARTIAL` |
| Report generation failure | `REPORT_FAILED` |

Do not expose raw exceptions, API keys, internal paths, or stack traces to the user.

## 11. Frontend/API Separation

The frontend must never directly call `http://localhost:8081/JSON/...`

Instead:

```text
Browser
   |
   v
Django API
   |
   v
ZAP Client
   |
   v
ZAP
```

The Django API should expose application-level endpoints such as:

- `POST /api/assessment/start/`
- `GET /api/assessment/status/`
- `POST /api/assessment/stop/`
- `GET /api/assessment/results/`
- `GET /api/assessment/report/`

The exact Django API routes can be determined during implementation.

These are NOT ZAP APIs. They are application APIs that the frontend uses.

## 12. User-Controlled vs Backend-Controlled Parameters

**User-controlled**

The POC should expose only:

- Target URL
- Active Scan Duration: 5, 10, 15, or 30 minutes
- Stop Active Scan
- Download HTML Report
- Download JSON Report

**Backend-controlled**

The following must never be user-configurable:

- ZAP host
- ZAP port
- ZAP API key
- ZAP API paths
- followRedirects
- Spider recurse setting
- Spider scan ID
- Active Scan ID
- Polling interval
- Report directory
- Report filename
- Report template
- Alert pagination
- Scan policy
- Attack strength
- Alert threshold

## 13. Important ZAP Workflow Concepts

The application must treat the ZAP components as separate operations.

- **Spider** = Discover application resources
- **Passive Scanner** = Analyze HTTP traffic without actively attacking
- **Active Scanner** = Actively test discovered/application resources
- **Alerts** = Security findings maintained by ZAP
- **Reports** = Generated representations of ZAP findings

Spider scan IDs and Active Scan IDs are operation-specific. For example, `Spider Scan ID = 0` and `Active Scan ID = 0` does not mean they are the same scan.

The application must store them separately.

## 14. Important Partial Scan Rule

If Active Scan reaches 100%, set:

```text
status = COMPLETED
completion = FULL
```

If the user stops the scan:

```text
status = STOPPED
completion = PARTIAL
```

If the configured maximum duration is reached:

```text
status = TIMEOUT
completion = PARTIAL
```

In both partial cases, the application may retrieve and display alerts already generated by ZAP. However, the results must clearly indicate that the assessment was not a complete Active Scan.

## 15. POC API Summary

| Stage | ZAP API | Purpose | Important Data |
|---|---|---|---|
| 2 | `core/action/accessUrl` | Verify target access | Access result |
| 3.1 | `spider/action/scan` | Start discovery | spiderScanId |
| 3.2 | `spider/view/status` | Monitor discovery | status |
| 3.3 | `spider/view/results` | Retrieve discovered URLs | results |
| 4.1 | `pscan/view/recordsToScan` | Monitor passive queue | recordsToScan |
| 5.0 | `ascan/action/setOptionMaxScanDurationInMins` | Set scan duration | Configuration result |
| 5.1 | `ascan/action/scan` | Start Active Scan | activeScanId |
| 5.2 | `ascan/view/status` | Monitor Active Scan | status |
| 5.3 | `ascan/action/stop` | Stop Active Scan | Stop result |
| 6.1 | `core/view/alerts` | Retrieve findings | Alerts |
| 6.2 | `core/view/alertsSummary` | Retrieve risk counts | Risk summary |
| 7.1 | `reports/view/templates` | Discover templates | Template list |
| 7.2 | `reports/action/generate` | Generate HTML/JSON | Report file |

## 16. Implementation Guidance

Implement the APIs incrementally.

Do not attempt to build the entire ZAP integration in a single Django view.

Create a dedicated ZAP client/service and keep the assessment workflow separate from the low-level API communication.

Recommended logical separation:

```text
Frontend
   |
   v
Django API Views
   |
   v
Assessment Workflow/Service
   |
   v
ZAP Client
   |
   v
OWASP ZAP
```

The ZAP client should handle ZAP-specific API communication.

The assessment workflow should handle:

- Current stage
- State transitions
- Polling
- Scan IDs
- Timeouts
- Stop operations
- Result processing
- Report generation

The frontend should focus on displaying application state and accepting the small number of user inputs defined in the project requirements.
