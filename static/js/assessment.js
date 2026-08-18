(function () {
    "use strict";

    const POLL_INTERVAL = 3000;

    const STAGES = [
        { id: "verify", label: "Target Verification", statuses: ["STARTING", "VERIFYING_TARGET"] },
        { id: "discovery", label: "Website Discovery", statuses: ["DISCOVERING"] },
        { id: "passive", label: "Passive Analysis", statuses: ["PASSIVE_SCANNING"] },
        { id: "active", label: "Active Security Testing", statuses: ["AWAITING_DURATION", "ACTIVE_SCANNING"] },
        { id: "findings", label: "Findings", statuses: ["ANALYZING_FINDINGS"] },
        { id: "report", label: "Report", statuses: ["COMPLETED", "STOPPED", "TIMEOUT"] },
    ];

    const LOADING_STATUSES = new Set([
        "STARTING",
        "VERIFYING_TARGET",
        "PASSIVE_SCANNING",
        "ANALYZING_FINDINGS",
    ]);

    const PROGRESS_STATUSES = new Set(["DISCOVERING"]);

    let pollTimer = null;
    let allFindings = [];
    let selectedDuration = null;
    let activeScanStartTime = null;
    let elapsedTimer = null;
    let lastStatus = null;

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

    function $(id) {
        return document.getElementById(id);
    }

    function show(el) {
        if (el) el.classList.remove("hidden");
    }

    function hide(el) {
        if (el) el.classList.add("hidden");
    }

    function setText(id, text) {
        const el = $(id);
        if (el) el.textContent = text;
    }

    function setHtml(id, html) {
        const el = $(id);
        if (el) el.innerHTML = html;
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function riskClass(risk) {
        const key = (risk || "").toLowerCase();
        if (key === "high") return "high";
        if (key === "medium") return "medium";
        if (key === "low") return "low";
        return "informational";
    }

    function setProgress(barId, textId, value, barWrapId) {
        const bar = $(barId);
        const text = $(textId);
        const pct = Math.min(100, Math.max(0, value || 0));
        if (bar) bar.style.width = pct + "%";
        if (text) text.textContent = pct + "%";
        const wrap = barWrapId ? $(barWrapId) : bar ? bar.closest(".progress-bar") : null;
        if (wrap) wrap.setAttribute("aria-valuenow", String(pct));
    }

    function formatElapsed(ms) {
        const totalSec = Math.floor(ms / 1000);
        const min = Math.floor(totalSec / 60);
        const sec = totalSec % 60;
        return String(min).padStart(2, "0") + ":" + String(sec).padStart(2, "0");
    }

    function startElapsedTimer() {
        stopElapsedTimer();
        activeScanStartTime = Date.now();
        elapsedTimer = setInterval(function () {
            if (activeScanStartTime) {
                setText("elapsed-time", "Elapsed: " + formatElapsed(Date.now() - activeScanStartTime));
            }
        }, 1000);
        setText("elapsed-time", "Elapsed: 00:00");
    }

    function stopElapsedTimer() {
        if (elapsedTimer) {
            clearInterval(elapsedTimer);
            elapsedTimer = null;
        }
        activeScanStartTime = null;
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

    function getStageIndex(status) {
        for (let i = 0; i < STAGES.length; i++) {
            if (STAGES[i].statuses.indexOf(status) !== -1) {
                return i;
            }
        }
        if (status === "FAILED") return -1;
        return -1;
    }

    function updateStageIndicator(status) {
        const currentIdx = getStageIndex(status);
        const failed = status === "FAILED";

        document.querySelectorAll(".stage-item").forEach(function (item) {
            const stageId = item.dataset.stage;
            const stageIdx = STAGES.findIndex(function (s) { return s.id === stageId; });

            item.classList.remove("stage-pending", "stage-current", "stage-completed", "stage-failed");

            if (failed && stageIdx === 0) {
                item.classList.add("stage-failed");
            } else if (currentIdx === -1) {
                item.classList.add("stage-pending");
            } else if (stageIdx < currentIdx) {
                item.classList.add("stage-completed");
            } else if (stageIdx === currentIdx) {
                item.classList.add("stage-current");
            } else {
                item.classList.add("stage-pending");
            }
        });
    }

    function updateProgressUI(data) {
        if (!data || data.status === "IDLE") {
            return;
        }

        setText("prog-id", data.application_scan_id || "—");
        setText("prog-target", data.target_url || "—");
        setText("prog-message", data.status_message || "");

        show($("progress-section"));
        updateStageIndicator(data.status);

        const loadingEl = $("loading-indicator");
        const progressDetail = $("progress-detail");
        const progressWrap = $("progress-bar-wrap");
        const discovered = $("discovered-count");

        const showLoading = LOADING_STATUSES.has(data.status);
        const showProgressBar = PROGRESS_STATUSES.has(data.status);

        if (showLoading) {
            show(loadingEl);
        } else {
            hide(loadingEl);
        }

        if (showProgressBar) {
            show(progressDetail);
            show(progressWrap);
            setText("progress-stage-title", "Website Discovery");
            setProgress("progress-bar", "progress-text", data.spider_progress);
        } else if (data.status === "ACTIVE_SCANNING") {
            hide(progressDetail);
        } else if (!showLoading) {
            hide(progressDetail);
        }

        if (data.discovered_url_count > 0) {
            show(discovered);
            discovered.textContent = data.discovered_url_count + " URLs discovered";
        } else {
            hide(discovered);
        }

        const durationSection = $("duration-section");
        const activeSection = $("active-section");

        if (data.awaiting_duration) {
            show(durationSection);
            hide(activeSection);
            selectedDuration = null;
            document.querySelectorAll(".btn-duration").forEach(function (btn) {
                btn.classList.remove("selected");
            });
            const startActiveBtn = $("start-active-btn");
            if (startActiveBtn) startActiveBtn.disabled = true;
        } else {
            hide(durationSection);
        }

        if (data.status === "ACTIVE_SCANNING") {
            show(activeSection);
            setProgress("active-progress-bar", "active-progress-text", data.active_scan_progress);
            if (lastStatus !== "ACTIVE_SCANNING") {
                startElapsedTimer();
            }
        } else {
            hide(activeSection);
            stopElapsedTimer();
        }

        lastStatus = data.status;

        if (data.status && data.status !== "IDLE") {
            hide($("start-section"));
        }

        if (data.has_results) {
            showResults(data);
        }

        if (data.is_final) {
            stopPolling();
            stopElapsedTimer();
        }

        if (data.status === "FAILED") {
            stopPolling();
            stopElapsedTimer();
            show($("start-section"));
            const err = $("start-error");
            if (err) {
                err.textContent = data.error_message || "The security assessment could not be completed.";
                show(err);
            }
        }
    }

    function showResults(data) {
        const section = $("results-section");
        show(section);

        setText("result-target", data.target_url || "—");
        setText("result-status", formatStatusLabel(data.status));
        setText("result-type", data.scan_completion === "FULL" ? "Full" : "Partial");

        const banner = $("result-banner");
        const icon = $("result-icon");
        const title = $("result-banner-title");
        const sub = $("result-banner-sub");

        banner.classList.remove("result-full", "result-partial", "result-failed");

        if (data.status === "COMPLETED") {
            banner.classList.add("result-full");
            icon.textContent = "\u2713";
            title.textContent = "Assessment Completed";
            sub.textContent = "Assessment Type: Full";
        } else if (data.status === "STOPPED" || data.status === "TIMEOUT") {
            banner.classList.add("result-partial");
            icon.textContent = "!";
            title.textContent = data.status === "STOPPED"
                ? "Active Scan Stopped"
                : "Active Scan Time Limit Reached";
            sub.textContent = "Assessment Type: Partial — findings may be incomplete.";
        } else {
            banner.classList.add("result-full");
            icon.textContent = "\u2713";
            title.textContent = "Assessment Results";
            sub.textContent = "";
        }

        const summary = data.alert_summary || {};
        const riskEl = $("risk-summary");
        if (riskEl) {
            riskEl.innerHTML = [
                ["HIGH", summary.high || 0, "high"],
                ["MEDIUM", summary.medium || 0, "medium"],
                ["LOW", summary.low || 0, "low"],
                ["INFORMATIONAL", summary.informational || 0, "informational"],
            ]
                .map(function (item) {
                    return (
                        '<div class="risk-item risk-' + item[2] + '">' +
                        '<span class="risk-label">' + item[0] + '</span>' +
                        '<span class="risk-count">' + item[1] + "</span></div>"
                    );
                })
                .join("");
        }

        const topEl = $("top-findings");
        if (topEl) {
            const items = data.top_findings || [];
            if (items.length === 0) {
                topEl.innerHTML = '<p class="status-note">No findings recorded for this target.</p>';
            } else {
                topEl.innerHTML = items
                    .map(function (f) {
                        const rc = riskClass(f.risk);
                        return (
                            '<article class="finding-card">' +
                            '<span class="finding-card-risk risk-text-' + rc + '">' +
                            escapeHtml(f.risk) + "</span>" +
                            '<p class="finding-card-name">' + escapeHtml(f.name) + "</p>" +
                            '<p class="finding-card-url">' + escapeHtml(f.url) + "</p>" +
                            (f.confidence
                                ? '<p class="finding-card-confidence">Confidence: ' +
                                  escapeHtml(f.confidence) + "</p>"
                                : "") +
                            "</article>"
                        );
                    })
                    .join("");
            }
        }
    }

    function formatStatusLabel(status) {
        const labels = {
            COMPLETED: "\u2713 Assessment Completed",
            STOPPED: "Active Scan Stopped",
            TIMEOUT: "Active Scan Time Limit Reached",
            FAILED: "Assessment Failed",
        };
        return labels[status] || status;
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
                hide($("results-section"));
                show($("all-findings-section"));
            })
            .catch(function (err) {
                showAlert("start-error", err.message);
            });
    }

    function renderFindingsTable() {
        const tbody = document.querySelector("#findings-table tbody");
        if (!tbody) return;

        tbody.innerHTML = allFindings
            .map(function (f, idx) {
                const rc = riskClass(f.risk);
                return (
                    "<tr data-idx='" + idx + "' tabindex='0'>" +
                    "<td><span class='risk-badge risk-badge-" + rc + "'>" +
                    escapeHtml(f.risk) + "</span></td>" +
                    "<td>" + escapeHtml(f.confidence) + "</td>" +
                    "<td>" + escapeHtml(f.name) + "</td>" +
                    "<td class='url-cell'>" + escapeHtml(f.url) + "</td></tr>"
                );
            })
            .join("");

        tbody.querySelectorAll("tr").forEach(function (row) {
            function selectRow() {
                tbody.querySelectorAll("tr").forEach(function (r) {
                    r.classList.remove("selected");
                });
                row.classList.add("selected");
                showFindingDetail(allFindings[parseInt(row.dataset.idx, 10)]);
            }
            row.addEventListener("click", selectRow);
            row.addEventListener("keydown", function (e) {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    selectRow();
                }
            });
        });
    }

    function showFindingDetail(f) {
        setText("detail-name", f.name);
        setText("detail-risk", f.risk);
        setText("detail-confidence", f.confidence);
        setText("detail-url", f.url);
        setText("detail-param", f.param || "\u2014");
        setText("detail-description", f.description || "\u2014");
        setText("detail-solution", f.solution || "\u2014");
        setText("detail-reference", f.reference || "\u2014");
        show($("finding-detail"));
    }

    function showAlert(id, message) {
        const el = $(id);
        if (el) {
            el.textContent = message;
            show(el);
        }
    }

    function downloadReport(format) {
        const errEl = $("report-error");
        const statusEl = $("report-status");
        hide(errEl);
        show(statusEl);
        statusEl.classList.remove("success");
        statusEl.textContent = "Generating " + format.toUpperCase() + " report...";

        fetch("/api/assessment/report/" + format + "/")
            .then(function (res) {
                if (!res.ok) {
                    return res.json().then(function (data) {
                        throw new Error(data.error || "The report could not be generated.");
                    });
                }
                return res.blob().then(function (blob) {
                    const disposition = res.headers.get("Content-Disposition") || "";
                    let filename = "report." + format;
                    const match = disposition.match(/filename="?([^"]+)"?/);
                    if (match) filename = match[1];

                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(url);

                    statusEl.textContent = "\u2713 " + format.toUpperCase() + " report ready";
                    statusEl.classList.add("success");
                });
            })
            .catch(function (err) {
                hide(statusEl);
                showAlert("report-error", err.message);
            });
    }

    function resetUI() {
        stopPolling();
        stopElapsedTimer();
        lastStatus = null;
        selectedDuration = null;

        show($("start-section"));
        hide($("progress-section"));
        hide($("duration-section"));
        hide($("active-section"));
        hide($("results-section"));
        hide($("all-findings-section"));
        hide($("finding-detail"));
        hide($("start-error"));
        hide($("report-status"));

        const targetInput = $("target_url");
        if (targetInput) targetInput.value = "";

        document.querySelectorAll(".btn-duration").forEach(function (btn) {
            btn.classList.remove("selected");
        });
        const startActiveBtn = $("start-active-btn");
        if (startActiveBtn) startActiveBtn.disabled = true;
    }

    function openStopModal() {
        show($("stop-modal"));
    }

    function closeStopModal() {
        hide($("stop-modal"));
    }

    document.addEventListener("DOMContentLoaded", function () {
        const startForm = $("start-form");
        if (startForm) {
            startForm.addEventListener("submit", function (e) {
                e.preventDefault();
                const url = $("target_url").value;
                hide($("start-error"));

                apiPost("/api/assessment/start/", { target_url: url })
                    .then(function (data) {
                        updateProgressUI(data);
                        startPolling();
                    })
                    .catch(function (err) {
                        showAlert("start-error", err.message);
                    });
            });
        }

        document.querySelectorAll(".btn-duration").forEach(function (btn) {
            btn.addEventListener("click", function () {
                selectedDuration = parseInt(btn.dataset.duration, 10);
                document.querySelectorAll(".btn-duration").forEach(function (b) {
                    b.classList.remove("selected");
                });
                btn.classList.add("selected");
                const startActiveBtn = $("start-active-btn");
                if (startActiveBtn) startActiveBtn.disabled = false;
                hide($("duration-error"));
            });
        });

        const startActiveBtn = $("start-active-btn");
        if (startActiveBtn) {
            startActiveBtn.addEventListener("click", function () {
                if (!selectedDuration) return;
                hide($("duration-error"));

                apiPost("/api/assessment/duration/", { duration: selectedDuration })
                    .then(function (data) {
                        updateProgressUI(data);
                    })
                    .catch(function (err) {
                        showAlert("duration-error", err.message);
                    });
            });
        }

        const stopBtn = $("stop-btn");
        if (stopBtn) {
            stopBtn.addEventListener("click", openStopModal);
        }

        $("stop-cancel-btn")?.addEventListener("click", closeStopModal);
        $("stop-modal-backdrop")?.addEventListener("click", closeStopModal);

        $("stop-confirm-btn")?.addEventListener("click", function () {
            closeStopModal();
            apiPost("/api/assessment/stop/", {})
                .then(refreshStatus)
                .catch(function (err) {
                    showAlert("report-error", err.message);
                });
        });

        $("view-all-btn")?.addEventListener("click", loadAllFindings);

        $("hide-findings-btn")?.addEventListener("click", function () {
            hide($("all-findings-section"));
            show($("results-section"));
        });

        $("download-html-btn")?.addEventListener("click", function () {
            downloadReport("html");
        });

        $("download-json-btn")?.addEventListener("click", function () {
            downloadReport("json");
        });

        $("new-assessment-btn")?.addEventListener("click", resetUI);

        refreshStatus();
    });
})();
