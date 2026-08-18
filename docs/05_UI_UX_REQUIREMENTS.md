# Web Security Assessment POC — UI/UX Requirements

## 1. Purpose

Define the user interface and user experience requirements for the POC.

The UI should be simple, professional, easy to understand, and suitable for demonstrating the OWASP ZAP security assessment workflow.

Visual polish, animations, and advanced styling should be added after the functional workflow is complete.

---

## 2. General UI Principles

The application should:

- Use a clean and modern security-focused design.
- Keep the interface simple and uncluttered.
- Clearly communicate the current assessment stage.
- Clearly distinguish completed, running, stopped, failed, and partial states.
- Use readable typography and consistent spacing.
- Provide clear buttons and status messages.
- Avoid exposing technical ZAP implementation details to users.
- Work well on a normal desktop/laptop browser.

Do not over-design the POC.

---

## 3. Application Layout

The application should have two primary user-facing screens:

```text
Landing Page
      |
      v
Assessment Dashboard
```

The results and report functionality can be displayed within the assessment dashboard rather than creating unnecessary additional pages.

## 4. Landing Page

The landing page is the first screen users see.

**Content**

Display:

- Application name
- Short description
- Brief explanation of the POC
- High-level assessment workflow
- Begin Security Assessment button

Example:

```text
+--------------------------------------------------------+
|                                                          |
|  Web Security Assessment                                |
|                                                          |
|  Automated web application security                     |
|  assessment powered by OWASP ZAP.                        |
|                                                          |
|  Target Verification → Discovery → Passive               |
|  Analysis → Active Testing → Findings → Report            |
|                                                          |
|  [ Begin Security Assessment ]                            |
|                                                          |
+--------------------------------------------------------+
```

Keep the content concise.

Do not display ZAP API configuration or technical implementation details.

## 5. Assessment Dashboard — Initial State

When the user enters the dashboard but has not started an assessment, display:

```text
+--------------------------------------------------------+
|  Security Assessment                                    |
|                                                          |
|  Target URL                                              |
|  [ https://example.com ]                                 |
|                                                          |
|  [ Start Assessment ]                                    |
|                                                          |
+--------------------------------------------------------+
```

**Target URL Input**

The input should:

- Have a clear label.
- Accept HTTP/HTTPS URLs.
- Provide a useful placeholder.
- Display validation errors clearly.
- Prevent submission when empty.

Example placeholder: `https://example.com`

## 6. Assessment Progress

After the user starts an assessment, the dashboard should transition into an assessment-progress view.

Display:

- Target URL
- Current stage
- Overall status
- Current progress where available
- Short human-readable status message

Example:

```text
Target
https://example.com

Current Stage
Website Discovery

Status
Discovering application pages...

Progress
████████████░░░░░░░░ 60%
```

Do not display raw ZAP API responses.

## 7. Assessment Stage Indicator

Provide a visual stage indicator.

Suggested stages:

1. Target Verification
2. Website Discovery
3. Passive Analysis
4. Active Security Testing
5. Findings
6. Report

Example:

```text
✓ Target Verification
✓ Website Discovery
● Passive Analysis
○ Active Security Testing
○ Findings
○ Report
```

Use visual states such as:

- Completed
- Current
- Pending
- Failed

The stage indicator should make it immediately clear where the assessment is currently running.

## 8. Target Verification UI

During Stage 2:

```text
Target Verification
Checking whether the target is reachable...
[ Loading indicator ]
```

On success:

```text
✓ Target is reachable
Continuing with website discovery...
```

On failure:

```text
✕ Target could not be reached
Please verify the URL and try again.
[ Try Again ]
```

Do not display the raw HTTP response body.

## 9. Spider / Website Discovery UI

During Spider:

```text
Website Discovery
Discovering application pages...
████████████░░░░░░░░ 60%
37 URLs discovered
```

When completed:

```text
✓ Website discovery completed
37 URLs discovered
```

The number of discovered URLs should be displayed when available.

Optionally provide:

```text
[ View Discovered URLs ]
```

This is optional for the first POC.

## 10. Passive Scanning UI

During passive scanning:

```text
Passive Security Analysis
Analyzing application traffic...
[ Loading indicator ]
Preparing active security testing...
```

When completed:

```text
✓ Passive security analysis completed
Preparing active security testing...
```

Do not display `recordsToScan = 0`.

Instead translate the technical value into a human-readable status.

Do not interpret zero pending records as zero vulnerabilities.

## 11. Active Scan Configuration UI

Before Active Scan begins, display a simple duration selector.

```text
Active Security Testing
Select maximum scan duration:

[ 5 min ] [ 10 min ] [ 15 min ] [ 30 min ]

[ Start Security Test ]
```

The user should not see or configure:

- ZAP scan ID
- ZAP API URL
- API key
- Scan policy
- Attack strength
- Other ZAP configuration

Do not provide an unlimited duration option in the initial POC.

## 12. Active Scan Progress UI

Once Active Scan starts:

```text
Active Security Testing
Testing the application for potential vulnerabilities...
██████████░░░░░░░░░░ 50%
Elapsed Time: 05:21

[ Stop Scan ]
```

The progress indicator should update automatically.

Use the ZAP Active Scan status to determine the percentage.

The user should not need to refresh the page.

## 13. Stop Active Scan

The Stop button should be clearly visible while Active Scan is running.

Example:

```text
[ Stop Scan ]
```

When clicked, optionally show a confirmation:

```text
Stop the active security test?
The current assessment will be treated as a
partial assessment.

[ Continue Scan ] [ Stop Scan ]
```

After stopping:

```text
Active scan stopped.
The available findings will now be analyzed.
Assessment type: Partial
```

Do not display the ZAP scan ID.

## 14. Active Scan Completion

When Active Scan reaches 100%:

```text
✓ Active security testing completed
Analyzing security findings...
```

Automatically proceed to the findings stage.

The user should not have to click a Continue button.

## 15. Assessment Results

After findings are retrieved, display a results summary.

Example:

```text
Security Assessment Results

Target
https://example.com

Status
✓ Assessment Completed
```

For a complete assessment: `Assessment Type: Full`

For a stopped or timed-out assessment: `Assessment Type: Partial`

## 16. Risk Summary

Display the alert summary prominently.

Example:

```text
Security Findings

+--------------+--------------+
| HIGH         | 2            |
+--------------+--------------+
| MEDIUM       | 5            |
+--------------+--------------+
| LOW          | 8            |
+--------------+--------------+
| INFORMATION  | 12           |
+--------------+--------------+
```

The visual treatment should make High and Medium findings easy to notice.

Do not use color as the only indicator of severity. Include the text labels.

## 17. Top Findings

Display the top five findings below the risk summary.

Example:

```text
Top Findings

1. High
   Example Vulnerability
   https://example.com/login

2. High
   Example Vulnerability
   https://example.com/search

3. Medium
   Example Vulnerability
   https://example.com/account
```

Each finding should display at minimum:

- Risk
- Finding name
- Affected URL

Optionally display:

- Confidence

## 18. View All Findings

Provide:

```text
[ View All Findings ]
```

The user should be able to see all target-specific findings in a readable table/list.

Suggested columns: Risk | Confidence | Finding | URL

Selecting a finding may open a detail section containing:

- Description
- Affected URL
- Parameter
- Confidence
- Solution
- Reference

Advanced filtering is not required for the initial POC.

## 19. Report Controls

After the assessment results are available, display:

```text
Reports

[ Download HTML Report ]
[ Download JSON Report ]
```

The user should not need to select ZAP templates.

The application internally uses:

- HTML → `traditional-html`
- JSON → `traditional-json`

Report generation should provide appropriate loading/error feedback.

Example:

```text
Generating HTML report...
```

After successful generation:

```text
✓ HTML report ready
[ Download HTML Report ]
```

## 20. Error States

All errors should be presented in clear, human-readable language.

Examples:

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
Please verify the URL and try again.
```

**Scan failure**

```text
The security assessment could not be completed.
Please try again.
```

**Report failure**

```text
The report could not be generated.
Please try again.
```

Do not display raw exceptions, stack traces, API keys, filesystem paths, or internal ZAP errors.

## 21. Loading States

Every long-running operation should provide visual feedback.

Use simple loading indicators for:

- Target verification
- Spider startup
- Passive scanning
- Active Scan startup
- Alert retrieval
- Report generation

Avoid making the user wonder whether the application is still working.

Example:

```text
Analyzing...
[ Loading indicator ]
```

## 22. Button Behavior

Buttons should clearly communicate their purpose.

Recommended primary actions:

- Begin Security Assessment
- Start Assessment
- Start Security Test
- Stop Scan
- View All Findings
- Download HTML Report
- Download JSON Report

Disable buttons when the associated action is unavailable.

For example:

- Disable Start Assessment while an assessment is running.
- Disable Stop Scan when Active Scan is not running.
- Disable report buttons while a report is being generated.

## 23. Assessment Status Messages

Use concise, human-readable status messages.

Suggested messages:

- Starting assessment...
- Checking target accessibility...
- Discovering application pages...
- Analyzing discovered traffic...
- Preparing active security testing...
- Active security testing in progress...
- Analyzing security findings...
- Assessment completed.
- Assessment stopped.
- Assessment reached the configured time limit.
- Assessment failed.
- Generating report...
- Report generated successfully.

Avoid technical messages such as:

```text
Calling /JSON/ascan/view/status/
scanId=0
recordsToScan=0
```

## 24. Full Assessment Screen Flow

The intended user experience is:

```text
Landing Page
      |
      v
Begin Security Assessment
      |
      v
Assessment Dashboard
      |
      v
Enter Target URL
      |
      v
Start Assessment
      |
      v
Target Verification
      |
      v
Website Discovery
      |
      v
Passive Analysis
      |
      v
Select Active Scan Duration
      |
      v
Active Security Testing
      |
      +------ Stop ------+
      |                  |
      v                  v
  Completed           Partial
      |                  |
      +--------+---------+
               |
               v
      Findings Analysis
               |
               v
      Assessment Results
               |
      +--------+--------+
      |                 |
      v                 v
View Findings      Generate Report
                          |
                +---------+---------+
                |                   |
                v                   v
          HTML Report         JSON Report
```

The workflow should progress automatically wherever possible.

## 25. Responsive Design

The application should work well on:

- Windows desktop
- Laptop browser
- Common desktop browser sizes

The initial POC does not require extensive mobile optimization.

However, the layout should avoid fixed widths that make the application unusable on smaller screens.

## 26. Visual Design

Use a professional cybersecurity-oriented visual style.

Recommended characteristics:

- Clean layout
- Strong visual hierarchy
- Consistent spacing
- Clear cards/panels
- Readable typography
- Subtle borders/shadows
- Clear status indicators
- Consistent button styling

Avoid:

- Excessive gradients
- Excessive animations
- Cluttered dashboards
- Too many colors
- Unnecessary charts
- Excessive decorative elements

The application should feel like a security assessment tool rather than a generic marketing website.

## 27. Animation Strategy

Animations are a Phase 3 enhancement.

Do not allow animations to interfere with functionality.

Potential animations:

- Page transitions
- Progress bar transitions
- Stage completion indicators
- Finding cards appearing
- Report generation/loading states

Animations should be subtle and short.

The functional workflow must work correctly even if animations are disabled.

## 28. Accessibility and Usability

The UI should follow basic accessibility practices:

- Use meaningful labels for inputs.
- Maintain readable text contrast.
- Do not rely only on color to communicate severity/status.
- Provide visible focus states.
- Use buttons for actions rather than clickable text where appropriate.
- Make progress/status information understandable without requiring knowledge of ZAP.

## 29. POC UI Priorities

Prioritize UI work in this order:

1. Clear workflow
2. Clear current-stage indication
3. Clear progress/status
4. Easy target URL input
5. Easy Active Scan duration selection
6. Clear findings summary
7. Easy report downloads
8. Visual polish
9. Animations

Do not spend significant development time on visual effects before the complete functional workflow works.

## 30. UI Non-Goals

The initial POC does not require:

- Login page
- User profile
- Admin dashboard
- Complex navigation
- Scan history
- Advanced charts
- Complex filtering
- Multi-user interface
- Mobile-first design
- Theme customization
- Dark/light mode switching
- Extensive settings pages
- User-configurable ZAP settings

Keep the UI focused on the core security assessment workflow.
