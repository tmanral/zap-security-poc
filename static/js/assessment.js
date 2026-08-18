(function () {
    "use strict";

    const POLL_INTERVAL = 3000;
    let pollTimer = null;
    let allFindings = [];

    function getCsrfToken() {
        const input = document.querySelector("[name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    function apiPost(url, body) {
        return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify(body || {}),
        }).then(async (res) => {
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || "Request failed");
            }
            return data;
        });
    }

    function apiGet(url) {
        return fetch(url).then(async (res) => {
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || "Request failed");
            }
            return data;
        });
    }

    function show(el) {
        if (el) el.classList.remove("hidden");
    }

    function hide(el) {
        if (el) el.classList.add("hidden");
    }

    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function setProgress(barId, textId, value) {
        const bar = document.getElementById(barId);
        const text = document.getElementById(textId);
        const pct = Math.min(100, Math.max(0, value || 0));
        if (bar) bar.style.width = pct + "%";
        if (text) text.textContent = pct + "%";
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function startPolling() {
        stopPolling();
        pollTimer = setInterval(refreshStatus, POLL_INTERVAL);
        refreshStatus();
    }

    function updateProgressUI(data) {
        setText("prog-id", data.application_scan_id || "—");
        setText("prog-target", data.target_url || "—");
        setText("prog-stage", data.stage || "—");
        setText("prog-status", data.status || "—");
        setText("prog-message", data.status_message || "");

        const progressSection = document.getElementById("progress-section");
        show(progressSection);

        const progressWrap = document.getElementById("progress-bar-wrap");
        const discovered = document.getElementById("discovered-count");

        if (data.status === "DISCOVERING") {
            show(progressWrap);
            setProgress("progress-bar", "progress-text", data.spider_progress);
        } else if (data.status === "ACTIVE_SCANNING") {
            hide(progressWrap);
        } else {
            hide(progressWrap);
        }

        if (data.discovered_url_count > 0) {
            show(discovered);
            discovered.textContent =
                data.discovered_url_count + " URLs discovered";
        } else {
            hide(discovered);
        }

        const durationSection = document.getElementById("duration-section");
        const activeSection = document.getElementById("active-section");

        if (data.awaiting_duration) {
            show(durationSection);
            hide(activeSection);
        } else {
            hide(durationSection);
        }

        if (data.status === "ACTIVE_SCANNING") {
            show(activeSection);
            setProgress(
                "active-progress-bar",
                "active-progress-text",
                data.active_scan_progress
            );
        } else {
            hide(activeSection);
        }

        const startSection = document.getElementById("start-section");
        if (data.status && data.status !== "IDLE") {
            hide(startSection);
        }

        if (data.has_results || data.is_final) {
            if (data.has_results) {
                showResults(data);
            }
            if (data.is_final) {
                stopPolling();
            }
        }

        if (data.status === "FAILED") {
            stopPolling();
            show(startSection);
            const err = document.getElementById("start-error");
            if (err) {
                err.textContent = data.error_message || "Assessment failed.";
                show(err);
            }
        }
    }

    function showResults(data) {
        const section = document.getElementById("results-section");
        show(section);

        setText("result-target", data.target_url || "—");
        setText("result-status", data.status || "—");

        const typeLabel =
            data.scan_completion === "FULL" ? "Full" : "Partial";
        setText("result-type", typeLabel);

        const summary = data.alert_summary || {};
        const riskEl = document.getElementById("risk-summary");
        if (riskEl) {
            riskEl.innerHTML = [
                ["HIGH", summary.high || 0],
                ["MEDIUM", summary.medium || 0],
                ["LOW", summary.low || 0],
                ["INFORMATIONAL", summary.informational || 0],
            ]
                .map(
                    ([label, count]) =>
                        '<div class="risk-item risk-' +
                        label.toLowerCase() +
                        '"><span>' +
                        label +
                        '</span><strong>' +
                        count +
                        "</strong></div>"
                )
                .join("");
        }

        const topEl = document.getElementById("top-findings");
        if (topEl) {
            const items = data.top_findings || [];
            topEl.innerHTML = items
                .map(function (f, i) {
                    return (
                        "<li><strong>" +
                        (i + 1) +
                        ". " +
                        escapeHtml(f.risk) +
                        "</strong> — " +
                        escapeHtml(f.name) +
                        "<br><span class='finding-url'>" +
                        escapeHtml(f.url) +
                        "</span></li>"
                    );
                })
                .join("");
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function refreshStatus() {
        apiGet("/api/assessment/status/")
            .then(updateProgressUI)
            .catch(function (err) {
                console.error("Status poll failed:", err);
            });
    }

    function loadAllFindings() {
        apiGet("/api/assessment/findings/")
            .then(function (data) {
                allFindings = data.findings || [];
                renderFindingsTable();
                hide(document.getElementById("results-section"));
                show(document.getElementById("all-findings-section"));
            })
            .catch(function (err) {
                alert(err.message);
            });
    }

    function renderFindingsTable() {
        const tbody = document.querySelector("#findings-table tbody");
        if (!tbody) return;
        tbody.innerHTML = allFindings
            .map(function (f, idx) {
                return (
                    "<tr data-idx='" +
                    idx +
                    "'><td>" +
                    escapeHtml(f.risk) +
                    "</td><td>" +
                    escapeHtml(f.confidence) +
                    "</td><td>" +
                    escapeHtml(f.name) +
                    "</td><td class='url-cell'>" +
                    escapeHtml(f.url) +
                    "</td></tr>"
                );
            })
            .join("");

        tbody.querySelectorAll("tr").forEach(function (row) {
            row.addEventListener("click", function () {
                const f = allFindings[parseInt(row.dataset.idx, 10)];
                showFindingDetail(f);
            });
        });
    }

    function showFindingDetail(f) {
        setText("detail-name", f.name);
        setText("detail-risk", f.risk);
        setText("detail-confidence", f.confidence);
        setText("detail-url", f.url);
        setText("detail-param", f.param || "—");
        setText("detail-description", f.description || "—");
        setText("detail-solution", f.solution || "—");
        setText("detail-reference", f.reference || "—");
        show(document.getElementById("finding-detail"));
    }

    function downloadReport(format) {
        const errEl = document.getElementById("report-error");
        hide(errEl);
        window.location.href = "/api/assessment/report/" + format + "/";
    }

    function resetUI() {
        stopPolling();
        show(document.getElementById("start-section"));
        hide(document.getElementById("progress-section"));
        hide(document.getElementById("duration-section"));
        hide(document.getElementById("active-section"));
        hide(document.getElementById("results-section"));
        hide(document.getElementById("all-findings-section"));
        hide(document.getElementById("finding-detail"));
        document.getElementById("target_url").value = "";
        hide(document.getElementById("start-error"));
    }

    document.addEventListener("DOMContentLoaded", function () {
        const startForm = document.getElementById("start-form");
        if (startForm) {
            startForm.addEventListener("submit", function (e) {
                e.preventDefault();
                const url = document.getElementById("target_url").value;
                const errEl = document.getElementById("start-error");
                hide(errEl);

                apiPost("/api/assessment/start/", { target_url: url })
                    .then(function (data) {
                        updateProgressUI(data);
                        startPolling();
                    })
                    .catch(function (err) {
                        errEl.textContent = err.message;
                        show(errEl);
                    });
            });
        }

        document.querySelectorAll(".btn-duration").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const duration = parseInt(btn.dataset.duration, 10);
                const errEl = document.getElementById("duration-error");
                hide(errEl);

                apiPost("/api/assessment/duration/", { duration: duration })
                    .then(function (data) {
                        updateProgressUI(data);
                    })
                    .catch(function (err) {
                        errEl.textContent = err.message;
                        show(errEl);
                    });
            });
        });

        const stopBtn = document.getElementById("stop-btn");
        if (stopBtn) {
            stopBtn.addEventListener("click", function () {
                if (
                    !confirm(
                        "Stop the active security test? The assessment will be treated as partial."
                    )
                ) {
                    return;
                }
                apiPost("/api/assessment/stop/", {})
                    .then(refreshStatus)
                    .catch(function (err) {
                        alert(err.message);
                    });
            });
        }

        const viewAllBtn = document.getElementById("view-all-btn");
        if (viewAllBtn) {
            viewAllBtn.addEventListener("click", loadAllFindings);
        }

        const hideFindingsBtn = document.getElementById("hide-findings-btn");
        if (hideFindingsBtn) {
            hideFindingsBtn.addEventListener("click", function () {
                hide(document.getElementById("all-findings-section"));
                show(document.getElementById("results-section"));
            });
        }

        const htmlBtn = document.getElementById("download-html-btn");
        if (htmlBtn) {
            htmlBtn.addEventListener("click", function () {
                downloadReport("html");
            });
        }

        const jsonBtn = document.getElementById("download-json-btn");
        if (jsonBtn) {
            jsonBtn.addEventListener("click", function () {
                downloadReport("json");
            });
        }

        const newBtn = document.getElementById("new-assessment-btn");
        if (newBtn) {
            newBtn.addEventListener("click", resetUI);
        }

        refreshStatus();
    });
})();
