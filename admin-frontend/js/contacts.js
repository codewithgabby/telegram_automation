
"use strict";

const CONTACTS_API_URL =
    "https://telegram-automation-nlq9.onrender.com/admin/contacts";

const CONTACTS_ACCESS_TOKEN_KEY = "admin_access_token";

let contacts = [];
let contactsLoaded = false;

let currentContactsPage = 1;
let contactsPerPage = 10;

async function contactsApiRequest(endpoint = "", options = {}) {

    const token = sessionStorage.getItem(CONTACTS_ACCESS_TOKEN_KEY);

    if (!token) {
        window.location.replace("index.html");
        throw new Error("Authentication required. Please sign in again.");
    }

    const headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`
    };

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${CONTACTS_API_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        sessionStorage.removeItem(CONTACTS_ACCESS_TOKEN_KEY);
        window.location.replace("index.html");
        throw new Error("Your session has expired. Please sign in again.");
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Unable to complete the request.");
    }

    return data;
}


// LOAD CONTACTS

async function loadContacts() {

    const container = document.getElementById("contactsList");

    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            <h3>Loading contacts...</h3>
            <p>Please wait.</p>
        </div>
    `;

    try {

        contacts = await contactsApiRequest("");

        contactsLoaded = true;

        updateContactStatistics();
        renderContacts();

    } catch (error) {

        console.error("Contact loading error:", error);

        container.textContent = error.message;
    }
}


// CONTACT STATISTICS

function updateContactStatistics() {

    const total = contacts.length;

    const paid = contacts.filter(
        contact => contact.payment_status === "paid"
    ).length;

    const booked = contacts.filter(
        contact => ["booked", "completed"].includes(contact.session_status)
    ).length;

    const pending = contacts.filter(
        contact => contact.follow_up?.status === "pending"
    ).length;

    document.getElementById("totalContacts").textContent = total;
    document.getElementById("paidContacts").textContent = paid;
    document.getElementById("bookedContacts").textContent = booked;
    document.getElementById("pendingFollowUps").textContent = pending;
}


// DATE FORMATTER

function formatContactDate(value) {

    if (!value) return "Not available";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) return "Not available";

    return date.toLocaleString();
}


// SAFE ELEMENT CREATION

function createContactElement(tag, className, text) {

    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined) {
        element.textContent = text;
    }

    return element;
}

// CONTACTS PAGINATION CONTROLS

function renderContactsPagination(totalItems, totalPages) {

    const container = document.getElementById("contactsList");

    if (!container) return;

    let pagination = document.getElementById("contactsPagination");

    if (!pagination) {
        pagination = createContactElement("div", "pagination-controls");
        pagination.id = "contactsPagination";
        container.insertAdjacentElement("afterend", pagination);
    }

    pagination.replaceChildren();

    if (totalItems === 0) {
        pagination.hidden = true;
        return;
    }

    pagination.hidden = false;

    const start = (currentContactsPage - 1) * contactsPerPage + 1;
    const end = Math.min(currentContactsPage * contactsPerPage, totalItems);

    const summary = createContactElement(
        "span",
        "pagination-summary",
        `Showing ${start}–${end} of ${totalItems} contacts`
    );

    const pageSize = createContactElement("select", "contact-select");

    [10, 20, 50].forEach(size => {

        const option = createContactElement("option", "", `${size} per page`);
        option.value = size;

        if (contactsPerPage === size) {
            option.selected = true;
        }

        pageSize.appendChild(option);
    });

    pageSize.addEventListener("change", () => {
        contactsPerPage = Number(pageSize.value);
        currentContactsPage = 1;
        renderContacts();
    });

    const previous = createContactElement(
        "button",
        "faq-action-button",
        "Previous"
    );

    previous.type = "button";
    previous.disabled = currentContactsPage === 1;

    previous.addEventListener("click", () => {
        currentContactsPage--;
        renderContacts();
    });

    const next = createContactElement(
        "button",
        "faq-action-button",
        "Next"
    );

    next.type = "button";
    next.disabled = currentContactsPage === totalPages;

    next.addEventListener("click", () => {
        currentContactsPage++;
        renderContacts();
    });

    const pageInfo = createContactElement(
        "span",
        "pagination-summary",
        `Page ${currentContactsPage} of ${totalPages}`
    );

    pagination.append(
        summary,
        pageSize,
        previous,
        pageInfo,
        next
    );
}


// RENDER CONTACTS

function renderContacts() {

    const container = document.getElementById("contactsList");

    if (!container) return;

    const searchTerm = (
        document.getElementById("contactSearch")?.value || ""
    ).toLowerCase().trim();

    const filter = document.getElementById("contactFilter")?.value || "all";

    let filtered = contacts.filter(contact => {

        const fullName = [
            contact.first_name,
            contact.last_name
        ].filter(Boolean).join(" ").toLowerCase();

        const username = (contact.username || "").toLowerCase();

        const telegramId = String(contact.telegram_user_id);

        const matchesSearch =
            fullName.includes(searchTerm) ||
            username.includes(searchTerm) ||
            telegramId.includes(searchTerm);

        if (!matchesSearch) return false;

        if (filter === "pending") {
            return contact.payment_status !== "paid";
        }

        if (filter === "paid") {
            return contact.payment_status === "paid";
        }

        if (filter === "booked") {
            return ["booked", "completed"].includes(contact.session_status);
        }

        if (filter === "followup") {
            return contact.follow_up?.status === "pending";
        }

        return true;
    });

    container.replaceChildren();

const totalPages = Math.max(
    1,
    Math.ceil(filtered.length / contactsPerPage)
);

currentContactsPage = Math.min(currentContactsPage, totalPages);

const startIndex = (currentContactsPage - 1) * contactsPerPage;

const pageContacts = filtered.slice(
    startIndex,
    startIndex + contactsPerPage
);

if (filtered.length === 0) {

    const empty = createContactElement("div", "empty-state");

    empty.append(
        createContactElement("h3", "", "No contacts found"),
        createContactElement(
            "p",
            "",
            "Try another search or check back when new enquiries arrive."
        )
    );

    container.appendChild(empty);

renderContactsPagination(0, 1);

return;
}

pageContacts.forEach(contact => {

        const card = createContactElement("article", "contact-card");

        const header = createContactElement("div", "contact-card-header");

        const name = [
            contact.first_name,
            contact.last_name
        ].filter(Boolean).join(" ") || "Telegram Contact";

        const identity = createContactElement("div", "contact-identity");

        identity.append(
            createContactElement("h3", "", name),
            createContactElement(
                "p",
                "",
                contact.username
                    ? `@${contact.username}`
                    : `Telegram ID: ${contact.telegram_user_id}`
            )
        );

        const welcomeStatus = createContactElement(
            "span",
            `contact-badge ${contact.welcome_status === "sent" ? "success" : "neutral"}`,
            `Welcome: ${contact.welcome_status || "unknown"}`
        );

        header.append(identity, welcomeStatus);

        const details = createContactElement("div", "contact-details");

        details.append(
            createContactElement(
                "p",
                "",
                `First enquiry: ${formatContactDate(contact.first_seen_at)}`
            ),
            createContactElement(
                "p",
                "",
                `Last activity: ${formatContactDate(contact.last_seen_at)}`
            ),
            createContactElement(
                "p",
                "",
                `Welcome sent: ${formatContactDate(contact.welcome_sent_at)}`
            )
        );

        const controls = createContactElement("div", "contact-controls");

        // PAYMENT

        const paymentGroup = createContactElement("div", "contact-control-group");

        paymentGroup.append(
            createContactElement("label", "", "Payment status")
        );

        const paymentSelect = createContactElement("select", "contact-select");

        [
            { value: "pending", label: "Pending" },
            { value: "paid", label: "Paid" }
        ].forEach(option => {

            const item = createContactElement("option", "", option.label);
            item.value = option.value;

            if (contact.payment_status === option.value) {
                item.selected = true;
            }

            paymentSelect.appendChild(item);
        });

        paymentSelect.addEventListener("change", () => {
            updateContactStatus(
                contact.id,
                "payment",
                { payment_status: paymentSelect.value }
            );
        });

        paymentGroup.appendChild(paymentSelect);

        // SESSION

        const sessionGroup = createContactElement("div", "contact-control-group");

        sessionGroup.append(
            createContactElement("label", "", "Session status")
        );

        const sessionSelect = createContactElement("select", "contact-select");

        [
            { value: "not_booked", label: "Not booked" },
            { value: "booked", label: "Booked" },
            { value: "completed", label: "Completed" }
        ].forEach(option => {

            const item = createContactElement("option", "", option.label);
            item.value = option.value;

            if (contact.session_status === option.value) {
                item.selected = true;
            }

            sessionSelect.appendChild(item);
        });

        sessionSelect.addEventListener("change", () => {
            updateContactStatus(
                contact.id,
                "session",
                { session_status: sessionSelect.value }
            );
        });

        sessionGroup.appendChild(sessionSelect);

        // FOLLOW-UP CONTROL

        const followGroup = createContactElement("div", "contact-control-group");

        followGroup.append(
            createContactElement("label", "", "Follow-up automation")
        );

        const followButton = createContactElement(
            "button",
            `faq-action-button ${contact.follow_up_enabled ? "toggle" : ""}`,
            contact.follow_up_enabled ? "Disable follow-ups" : "Enable follow-ups"
        );

        followButton.type = "button";

        followButton.addEventListener("click", () => {

            const enabled = !contact.follow_up_enabled;

            const message = enabled
                ? "Enable follow-ups for this contact?"
                : "Disable follow-ups for this contact?";

            if (!confirm(message)) return;

            updateContactStatus(
                contact.id,
                "follow-ups",
                { enabled }
            );
        });

        followGroup.appendChild(followButton);

        controls.append(paymentGroup, sessionGroup, followGroup);


        // FOLLOW-UP HISTORY

        const history = createContactElement("div", "followup-history");

        const followUp = contact.follow_up;

        history.append(
            createContactElement("h4", "", "Follow-up information")
        );

        if (followUp) {

            const isCancelled = followUp.status === "cancelled";
            const wasReplied = followUp.response === "replied";

            history.append(
                createContactElement(
                    "p",
                    "",
                    `Status: ${followUp.status || "Unknown"}`
                ),
                createContactElement(
                    "p",
                    "",
                    `${isCancelled ? "Originally scheduled" : "Scheduled"}: ${formatContactDate(followUp.scheduled_at)}`
                ),
                createContactElement(
                    "p",
                    "",
                    `Sent: ${formatContactDate(followUp.sent_at)}`
                ),
                createContactElement(
                    "p",
                    "",
                    `Client response: ${
                        wasReplied
                            ? "Replied"
                            : followUp.response === "interested"
                                ? "Interested"
                                : followUp.response === "not_now"
                                    ? "Not right now"
                                    : "No response"
                    }`
                )
            );

            if (followUp.last_error) {
                history.appendChild(
                    createContactElement(
                        "p",
                        "contact-error",
                        `Note: ${followUp.last_error}`
                    )
                );
            }

        } else {

            history.appendChild(
                createContactElement(
                    "p",
                    "",
                    "No follow-up record available."
                )
            );
        }

        card.append(header, details, controls, history);

        container.appendChild(card);
    });

    renderContactsPagination(filtered.length, totalPages);
}



// UPDATE CONTACT STATUS

async function updateContactStatus(contactId, action, payload) {

    try {

        await contactsApiRequest(`/${contactId}/${action}`, {
            method: "PATCH",
            body: JSON.stringify(payload)
        });

        await loadContacts();

    } catch (error) {

        console.error("Contact update error:", error);

        alert(error.message);

        await loadContacts();
    }
}


// INITIALIZE CONTACT DASHBOARD

document.addEventListener("DOMContentLoaded", () => {

    document.getElementById("refreshContactsButton")
        ?.addEventListener("click", loadContacts);

    document.getElementById("contactSearch")
        ?.addEventListener("input", () => {
            currentContactsPage = 1;
            renderContacts();
        });

    document.getElementById("contactFilter")
        ?.addEventListener("change", () => {
            currentContactsPage = 1;
            renderContacts();
        });

    document.addEventListener("adminAuthenticated", () => {
        if (
            document.getElementById("contacts")?.classList.contains("active")
        ) {
            loadContacts();
        }
    });

});
