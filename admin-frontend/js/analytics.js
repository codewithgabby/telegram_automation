
"use strict";

// =============================================
// ANALYTICS DASHBOARD
// =============================================

// Reuses API_BASE_URL and getAccessToken()
// from the existing auth.js file.

document.addEventListener("DOMContentLoaded", () => {

    const periodSelect = document.getElementById("analyticsPeriod");
    const customDateRange = document.getElementById("customDateRange");
    const startDate = document.getElementById("analyticsStartDate");
    const endDate = document.getElementById("analyticsEndDate");
    const applyDatesButton = document.getElementById("applyAnalyticsDates");
    const refreshButton = document.getElementById("refreshAnalyticsButton");

    if (!periodSelect) return;

    let currentCustomRange = null;

    // =============================================
    // API REQUEST HELPER
    // =============================================

    async function fetchAnalytics(endpoint) {

        const token = getAccessToken();

        if (!token) {
            throw new Error("Your admin session has expired. Please sign in again.");
        }

        const response = await fetch(
            `${API_BASE_URL}/admin/analytics/${endpoint}`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to retrieve analytics data."
            );
        }

        return data;
    }


    // =============================================
    // DATE FILTER
    // =============================================

    function getDateQuery() {

        if (periodSelect.value === "custom") {

            if (!currentCustomRange) {
                throw new Error("Please apply your custom date range.");
            }

            const params = new URLSearchParams();

            params.set(
                "start_date",
                `${currentCustomRange.start}T00:00:00Z`
            );

            // End date is exclusive, so add one day.
            const exclusiveEnd = new Date(
                `${currentCustomRange.end}T00:00:00Z`
            );

            exclusiveEnd.setUTCDate(
                exclusiveEnd.getUTCDate() + 1
            );

            params.set(
                "end_date",
                exclusiveEnd.toISOString()
            );

            return params.toString();
        }

        return `days=${periodSelect.value}`;
    }


    // =============================================
    // PERFORMANCE STATISTICS
    // =============================================

    function updateStatistics(data) {

        document.getElementById("analyticsEnquiries").textContent =
            data.new_enquiries ?? 0;

        document.getElementById("analyticsWelcomes").textContent =
            data.welcome_delivered ?? 0;

        document.getElementById("analyticsReplies").textContent =
            data.client_replies ?? 0;

        document.getElementById("analyticsInterested").textContent =
            data.interested_leads ?? 0;

        document.getElementById("analyticsPaid").textContent =
            data.paid_clients ?? 0;

        document.getElementById("analyticsCompleted").textContent =
            data.completed_sessions ?? 0;
    }


    // =============================================
    // ENQUIRY TREND CHART
    // =============================================

    function renderEnquiryTrends(records) {

        const container = document.getElementById(
            "enquiryTrendsChart"
        );

        if (!records.length) {

            container.innerHTML =
                "<p>No enquiry records found for this period.</p>";

            return;
        }

        const maximum = Math.max(
            ...records.map(item => item.total),
            1
        );

        container.innerHTML = `
            <div style="
                display:flex;
                align-items:flex-end;
                gap:12px;
                width:100%;
                height:200px;
                overflow-x:auto;
                padding:10px 5px;
            ">
                ${records.map(item => {

                    const height = Math.max(
                        (item.total / maximum) * 150,
                        4
                    );

                    return `
                        <div style="
                            flex:1;
                            min-width:35px;
                            height:100%;
                            display:flex;
                            flex-direction:column;
                            justify-content:flex-end;
                            align-items:center;
                            gap:8px;
                        ">
                            <strong style="font-size:12px;">
                                ${item.total}
                            </strong>

                            <div style="
                                width:100%;
                                max-width:38px;
                                height:${height}px;
                                background:#2563eb;
                                border-radius:6px 6px 0 0;
                            "></div>

                            <span style="
                                font-size:10px;
                                color:#64748b;
                                white-space:nowrap;
                            ">
                                ${item.date.slice(5)}
                            </span>
                        </div>
                    `;
                }).join("")}
            </div>
        `;
    }


    // =============================================
    // CONVERSION OVERVIEW
    // =============================================


function renderConversions(data) {
    const container = document.getElementById("conversionChart");

    const periodStages = [
        { label: "New Enquiries", value: data.enquiries },
        { label: "Welcome Delivered", value: data.welcome_delivered },
        { label: "Client Replies", value: data.client_replies },
        { label: "Interested Leads", value: data.interested_leads }
    ];

    const currentStages = [
        { label: "Currently Paid Clients", value: data.paid_clients },
        { label: "Currently Completed Sessions", value: data.completed_sessions }
    ];

    const maximum = Math.max(
        ...periodStages.map(stage => stage.value || 0),
        ...currentStages.map(stage => stage.value || 0),
        1
    );

    function renderStages(stages) {
        return stages.map(stage => {
            const value = stage.value || 0;
            const percentage = (value / maximum) * 100;

            return `
                <div style="margin-bottom:16px;">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        gap:10px;
                        margin-bottom:6px;
                        font-size:13px;
                    ">
                        <span>${stage.label}</span>
                        <strong>${value}</strong>
                    </div>

                    <div style="
                        height:9px;
                        background:#e5e7eb;
                        border-radius:10px;
                        overflow:hidden;
                    ">
                        <div style="
                            height:100%;
                            width:${percentage}%;
                            background:#2563eb;
                            border-radius:10px;
                        "></div>
                    </div>
                </div>
            `;
        }).join("");
    }

    container.innerHTML = `
        <div style="width:100%;">
            <h4>Selected Reporting Period</h4>
            ${renderStages(periodStages)}

            <hr style="margin:20px 0;">

            <h4>Current Business Status</h4>
            <p style="font-size:12px;color:#64748b;">
                Current statuses across all registered contacts.
            </p>

            ${renderStages(currentStages)}
        </div>
    `;
}



    // =============================================
    // RECENT CLIENT ACTIVITY
    // =============================================

    function renderRecentActivity(records) {

        const container = document.getElementById(
            "analyticsActivityList"
        );

        if (!records.length) {

            container.innerHTML = `
                <div class="empty-state">
                    <h3>No activity records yet</h3>
                    <p>
    New client engagement activities will appear here as they occur.
</p>
                </div>
            `;

            return;
        }

        container.innerHTML = records.map(activity => {

            const name = escapeHTML(activity.client_name);

            const description = escapeHTML(
                activity.description || activity.event_type
            );

            const date = new Date(
                activity.occurred_at
            ).toLocaleString();

            return `
                <div style="
                    padding:15px 0;
                    border-bottom:1px solid #e5e7eb;
                ">

                    <strong>${name}</strong>

                    <p style="margin:6px 0;">
                        ${description}
                    </p>

                    <small style="color:#64748b;">
                        ${date}
                    </small>

                </div>
            `;

        }).join("");
    }


    // =============================================
    // HTML ESCAPING
    // =============================================

    function escapeHTML(value) {

        return String(value).replace(
            /[&<>"']/g,
            character => ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            })[character]
        );
    }


    // =============================================
    // LOAD ANALYTICS
    // =============================================

    async function loadAnalytics() {

        try {

            refreshButton.disabled = true;
            refreshButton.textContent = "Loading...";

            const dateQuery = getDateQuery();

            const [
                summary,
                trends,
                conversions,
                activity
            ] = await Promise.all([

                fetchAnalytics(`summary?${dateQuery}`),

                fetchAnalytics(`trends?${dateQuery}`),

                fetchAnalytics(`conversions?${dateQuery}`),

                fetchAnalytics("activity?limit=20")

            ]);

            updateStatistics(summary);

            renderEnquiryTrends(
                trends.trends || []
            );

            renderConversions(conversions);

            renderRecentActivity(
                activity.activities || []
            );

        } catch (error) {

            console.error("Analytics loading error:", error);

            document.getElementById(
                "enquiryTrendsChart"
            ).innerHTML = `<p>${escapeHTML(error.message)}</p>`;

            document.getElementById(
                "conversionChart"
            ).innerHTML = `<p>${escapeHTML(error.message)}</p>`;

        } finally {

            refreshButton.disabled = false;
            refreshButton.textContent = "↻ Refresh Analytics";

        }
    }


    // =============================================
    // PERIOD SELECTION
    // =============================================

    periodSelect.addEventListener("change", () => {

        const isCustom = periodSelect.value === "custom";

        customDateRange.hidden = !isCustom;

        if (!isCustom) {

            currentCustomRange = null;

            loadAnalytics();
        }
    });


    // =============================================
    // APPLY CUSTOM DATE RANGE
    // =============================================

    applyDatesButton?.addEventListener("click", () => {

        if (!startDate.value || !endDate.value) {

            alert("Please select both start and end dates.");

            return;
        }

        if (startDate.value > endDate.value) {

            alert("The start date cannot be later than the end date.");

            return;
        }

        currentCustomRange = {
            start: startDate.value,
            end: endDate.value
        };

        loadAnalytics();
    });


    // =============================================
    // REFRESH ANALYTICS
    // =============================================

    refreshButton?.addEventListener(
        "click",
        loadAnalytics
    );


    // =============================================
    // INITIALIZE AFTER ADMIN AUTHENTICATION
    // =============================================

    document.addEventListener(
        "adminAuthenticated",
        loadAnalytics
    );

});
