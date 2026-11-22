"use strict";

const STRATEGY_API = `${API_BASE_URL}/admin/strategy`;

let strategyLoaded = false;
let strategyServices = [];
let strategySections = [];
let strategySettings = [];

// Strategy bookings pagination
let strategyBookingsPage = 1;
const STRATEGY_BOOKINGS_PAGE_SIZE = 10;
let strategyBookingsTotal = 0;

function strategyHeaders(json = true) {
    const headers = {
        Authorization: `Bearer ${getAccessToken()}`
    };

    if (json) {
        headers["Content-Type"] = "application/json";
    }

    return headers;
}

async function strategyRequest(path, options = {}) {
    const response = await fetch(`${STRATEGY_API}${path}`, {
        ...options,
        headers: {
            ...strategyHeaders(options.body !== undefined),
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.detail || `Request failed (${response.status})`
        );
    }

    return data;
}

function strategyArray(data, keys = []) {
    if (Array.isArray(data)) {
        return data;
    }

    for (const key of keys) {
        if (Array.isArray(data?.[key])) {
            return data[key];
        }
    }

    return [];
}

function strategyEscape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}

function strategyMoney(value) {
    return `₦${Number(value || 0).toLocaleString("en-NG")}`;
}

function strategyDateTime(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return strategyEscape(value);
    }

    return date.toLocaleString("en-NG", {
        timeZone: "Africa/Lagos",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });
}

function strategyMessage(message, isError = false) {
    const element = document.getElementById("strategyMessage");

    if (!element) {
        return;
    }

    element.textContent = message;
    element.classList.toggle("error", isError);
    element.classList.add("visible");

    window.setTimeout(() => {
        element.classList.remove("visible");
    }, 5000);
}

function strategyEmpty(message) {
    return `
        <div class="empty-state">
            <p>${strategyEscape(message)}</p>
        </div>
    `;
}

// --------------------------------------------------
// MAIN LOADER
// --------------------------------------------------

async function loadStrategyDashboard() {
    try {
        await Promise.all([
            loadStrategyServices(),
            loadStrategySections(),
            loadStrategySettings()
        ]);

        strategyLoaded = true;
    } catch (error) {
        console.error("Strategy dashboard loading error:", error);
        strategyMessage(error.message, true);
    }
}

// --------------------------------------------------
// PACKAGES / SERVICES
// --------------------------------------------------

async function loadStrategyServices() {
    const container = document.getElementById("strategyServicesList");

    if (!container) {
        return;
    }

    const data = await strategyRequest("/services");

    strategyServices = strategyArray(
        data,
        ["services", "items", "results"]
    );

    if (!strategyServices.length) {
        container.innerHTML = strategyEmpty(
            "No consultation packages have been created."
        );
        return;
    }

    container.innerHTML = strategyServices.map((service) => `
        <article class="strategy-record">

            <div class="strategy-record-main">

                <div class="strategy-record-title">
                    <h4>${strategyEscape(service.name)}</h4>

                    <span class="strategy-status ${
                        service.is_active
                            ? "status-active"
                            : "status-inactive"
                    }">
                        ${service.is_active ? "Active" : "Inactive"}
                    </span>
                </div>

                <p>${strategyEscape(service.description)}</p>

                <div class="strategy-record-meta">
                    <strong>${strategyMoney(service.price_ngn)}</strong>
                    <span>${Number(service.session_count || 1)} session(s)</span>
                    <span>${Number(service.duration_minutes || 0)} minutes each</span>
                    <span>Order: ${Number(service.display_order || 0)}</span>
                </div>

                ${
                    Array.isArray(service.features) && service.features.length
                        ? `
                            <ul>
                                ${service.features.map(item => `
                                    <li>${strategyEscape(item)}</li>
                                `).join("")}
                            </ul>
                        `
                        : ""
                }

            </div>

            <div class="strategy-record-actions">
                <button
                    class="secondary-button"
                    data-service-edit="${strategyEscape(service.id)}"
                >
                    Edit
                </button>
            </div>

        </article>
    `).join("");

    container.querySelectorAll("[data-service-edit]").forEach((button) => {
        button.addEventListener("click", () => {
            const service = strategyServices.find(
                item => String(item.id) === button.dataset.serviceEdit
            );

            if (service) {
                openStrategyPackageModal(service);
            }
        });
    });
}

function openStrategyPackageModal(service = null) {
    const form = document.getElementById("strategyPackageForm");

    form.reset();

    document.getElementById("strategyPackageModalTitle").textContent =
        service ? "Edit Consultation Package" : "Add Consultation Package";

    document.getElementById("strategyPackageId").value = service?.id || "";
    const codeInput = document.getElementById("strategyPackageCode");
    codeInput.value = service?.code || "";
    codeInput.readOnly = Boolean(service);
    codeInput.required = !service;

    document.getElementById("strategyPackageName").value = service?.name || "";
    document.getElementById("strategyPackageDescription").value = service?.description || "";
    document.getElementById("strategyPackagePrice").value = service?.price_ngn ?? "";
    document.getElementById("strategyPackageSessions").value = service?.session_count ?? 1;
    document.getElementById("strategyPackageDuration").value = service?.duration_minutes ?? 60;
    document.getElementById("strategyPackageFeatures").value =
        (service?.features || []).join("\n");
    document.getElementById("strategyPackageOrder").value = service?.display_order ?? 0;
    document.getElementById("strategyPackageActive").value =
        String(service?.is_active ?? true);

    document.getElementById("strategyPackageModal").classList.add("active");
}

function closeStrategyPackageModal() {
    document.getElementById("strategyPackageModal").classList.remove("active");
}

async function saveStrategyPackage(event) {
    event.preventDefault();

    const id = document.getElementById("strategyPackageId").value;
    const code = document.getElementById("strategyPackageCode").value;

    const payload = {
        name: document.getElementById("strategyPackageName").value.trim(),
        description: document.getElementById("strategyPackageDescription").value.trim(),
        price_ngn: Number(document.getElementById("strategyPackagePrice").value),
        session_count: Number(document.getElementById("strategyPackageSessions").value),
        duration_minutes: Number(document.getElementById("strategyPackageDuration").value),
        features: document.getElementById("strategyPackageFeatures").value
            .split("\n")
            .map(item => item.trim())
            .filter(Boolean),
        display_order: Number(document.getElementById("strategyPackageOrder").value),
        is_active: document.getElementById("strategyPackageActive").value === "true"
    };

    if (
        !payload.name ||
        !payload.description ||
        !Number.isInteger(payload.price_ngn) ||
        payload.price_ngn <= 0 ||
        !Number.isInteger(payload.session_count) ||
        payload.session_count < 1 ||
        !Number.isInteger(payload.duration_minutes) ||
        payload.duration_minutes < 1 ||
        !Number.isFinite(payload.display_order)
    ) {
        strategyMessage("Please check the package details and enter valid values.", true);
        return;
    }

    const button = document.getElementById("saveStrategyPackageButton");
    button.disabled = true;
    button.textContent = "Saving...";

    try {
        if (id) {
            await strategyRequest(`/services/${encodeURIComponent(id)}`, {
                method: "PATCH",
                body: JSON.stringify(payload)
            });

            strategyMessage("Package updated successfully.");
        } else {
            await strategyRequest("/services", {
                method: "POST",
                body: JSON.stringify({
                    ...payload,
                    code: code.trim()
                })
            });

            strategyMessage("Package created successfully.");
        }

        closeStrategyPackageModal();
        await loadStrategyServices();

    } catch (error) {
        strategyMessage(error.message, true);
    } finally {
        button.disabled = false;
        button.textContent = "Save Package";
    }
}

// --------------------------------------------------
// WEBSITE CONTENT SECTIONS
// --------------------------------------------------

async function loadStrategySections() {
    const container = document.getElementById("strategyContentList");

    if (!container) {
        return;
    }

    const data = await strategyRequest("/sections");

    strategySections = strategyArray(
        data,
        ["sections", "items", "results"]
    );

    if (!strategySections.length) {
        container.innerHTML = strategyEmpty(
            "No website content sections have been created."
        );
        return;
    }

    container.innerHTML = strategySections.map((section) => `
        <article class="strategy-record">

            <div class="strategy-record-main">

                <div class="strategy-record-title">
                    <h4>${strategyEscape(section.title)}</h4>

                    <span class="strategy-status ${
                        section.is_active
                            ? "status-active"
                            : "status-inactive"
                    }">
                        ${section.is_active ? "Active" : "Inactive"}
                    </span>
                </div>

                <p>
                    <strong>Key:</strong>
                    ${strategyEscape(section.section_key)}
                </p>

                ${
                    section.eyebrow
                        ? `<p>${strategyEscape(section.eyebrow)}</p>`
                        : ""
                }

                <p>${strategyEscape(section.body)}</p>

                <div class="strategy-record-meta">
                    <span>
                        Display order: ${Number(section.display_order || 0)}
                    </span>
                </div>

            </div>

            <div class="strategy-record-actions">
                <button
                    class="secondary-button"
                    data-section-edit="${strategyEscape(section.id)}"
                >
                    Edit
                </button>
            </div>

        </article>
    `).join("");

    container.querySelectorAll("[data-section-edit]").forEach((button) => {
        button.addEventListener("click", () => {
            const section = strategySections.find(
                item => String(item.id) === button.dataset.sectionEdit
            );

            if (section) {
                editStrategySection(section);
            }
        });
    });
}

function createStrategySection() {
    openStrategyContentModal();
}

function editStrategySection(section) {
    openStrategyContentModal(section);
}

// --------------------------------------------------
// WEBSITE CONTENT MODAL
// --------------------------------------------------

function openStrategyContentModal(section = null) {
    const modal = document.getElementById("strategyContentModal");
    const form = document.getElementById("strategyContentForm");

    if (!modal || !form) {
        strategyMessage(
            "Website Content modal not found. Check dashboard.html.",
            true
        );
        return;
    }

    form.reset();

    document.getElementById("strategyContentModalTitle").textContent =
        section ? "Edit Website Content" : "Add Website Content";

    document.getElementById("strategyContentId").value =
        section?.id || "";

    const keyInput = document.getElementById("strategyContentKey");

    keyInput.value = section?.section_key || "";
    keyInput.readOnly = Boolean(section);

    document.getElementById("strategyContentTitle").value =
        section?.title || "";

    document.getElementById("strategyContentEyebrow").value =
        section?.eyebrow || "";

    document.getElementById("strategyContentBody").value =
        section?.body || "";

    document.getElementById("strategyContentOrder").value =
        section?.display_order ?? 0;

    document.getElementById("strategyContentActive").value =
        String(section?.is_active ?? true);

    modal.classList.add("active");
}

function closeStrategyContentModal() {
    document.getElementById("strategyContentModal")
        ?.classList.remove("active");
}

async function saveStrategyContent(event) {
    event.preventDefault();

    const id = document.getElementById("strategyContentId").value;

    const sectionKey = document
        .getElementById("strategyContentKey")
        .value.trim();

    const title = document
        .getElementById("strategyContentTitle")
        .value.trim();

    const eyebrow = document
        .getElementById("strategyContentEyebrow")
        .value.trim();

    const body = document
        .getElementById("strategyContentBody")
        .value.trim();

    const order = Number(
        document.getElementById("strategyContentOrder").value
    );

    const isActive =
        document.getElementById("strategyContentActive").value === "true";

    if (!id && !sectionKey) {
        strategyMessage("Section key is required.", true);
        return;
    }

    if (!title || !body || !Number.isInteger(order) || order < 0) {
        strategyMessage(
            "Enter a valid title, body and display order.",
            true
        );
        return;
    }

    const payload = {
        title,
        eyebrow: eyebrow || null,
        body,
        is_active: isActive,
        display_order: order
    };

    if (!id) {
        payload.section_key = sectionKey;
    }

    const button = document.getElementById(
        "saveStrategyContentButton"
    );

    if (!button) {
        strategyMessage("Save button not found.", true);
        return;
    }

    button.disabled = true;
    button.textContent = "Saving...";

    try {
        if (id) {
            await strategyRequest(
                `/sections/${encodeURIComponent(id)}`,
                {
                    method: "PATCH",
                    body: JSON.stringify(payload)
                }
            );

            strategyMessage("Website content updated successfully.");
        } else {
            await strategyRequest("/sections", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            strategyMessage("Website content created successfully.");
        }

        closeStrategyContentModal();

        await loadStrategySections();

    } catch (error) {
        console.error("Website content save error:", error);
        strategyMessage(error.message, true);

    } finally {
        button.disabled = false;
        button.textContent = "Save Content";
    }
}

// --------------------------------------------------
// WEBSITE SETTINGS
// --------------------------------------------------

const PUBLIC_SITE_SETTING_KEY = "public_site";

const PAYMENT_BANK_DETAILS_SETTING_KEY = "payment_bank_details";

const DEFAULT_PUBLIC_SITE_SETTINGS = {
    brand_name: "GABRIEL JOHNSON",
    brand_subtitle: "IMMIGRATION STRATEGY SERVICES",
    support_url: "https://t.me/CodewithGabby",
    contact_label: "Contact Gabe directly",
    footer_name: "Gabriel Johnson",
    footer_brand: "Immigration Strategy Services",
    footer_tagline: "Canada-focused immigration guidance · Worldwide bookings"
};

async function loadStrategySettings() {
    const container = document.getElementById("strategySettingsList");

    if (!container) {
        return;
    }

    const data = await strategyRequest("/settings");

    strategySettings = strategyArray(
        data,
        ["settings", "items", "results"]
    );

    const publicSiteSetting = strategySettings.find(
        setting => setting.key === PUBLIC_SITE_SETTING_KEY
    );

    const publicSite = {
        ...DEFAULT_PUBLIC_SITE_SETTINGS,
        ...(publicSiteSetting?.value || {})
    };

    container.innerHTML = `
        <article class="strategy-record">
            <div class="strategy-record-main">
                <div class="strategy-record-title">
                    <h4>Public Website Identity</h4>

                    <span class="strategy-status ${
                        publicSiteSetting?.is_public
                            ? "status-active"
                            : "status-inactive"
                    }">
                        ${publicSiteSetting?.is_public ? "Public" : "Not published"}
                    </span>
                </div>

                <p>
                    Manage the brand identity, contact link and footer
                    displayed on your public strategy website.
                </p>

                <div class="strategy-record-meta">
                    <span>Brand: ${strategyEscape(publicSite.brand_name)}</span>
                    <span>Contact: ${strategyEscape(publicSite.contact_label)}</span>
                </div>
            </div>

            <div class="strategy-record-actions">
                <button
                    class="secondary-button"
                    id="editPublicSiteSettingsButton"
                    type="button"
                >
                    ${publicSiteSetting ? "Edit Settings" : "Set Up Website Identity"}
                </button>
            </div>
        </article>

        ${
            (() => {
                const bankSetting = strategySettings.find(
                    setting => setting.key === PAYMENT_BANK_DETAILS_SETTING_KEY
                );

                const bank = bankSetting?.value || {};

                return `
                    <article class="strategy-record">
                        <div class="strategy-record-main">
                            <div class="strategy-record-title">
                                <h4>Payment Bank Details</h4>

                                <span class="strategy-status ${
                                    bankSetting?.is_public
                                        ? "status-active"
                                        : "status-inactive"
                                }">
                                    ${bankSetting?.is_public ? "Public" : "Private"}
                                </span>
                            </div>

                            <p><strong>Bank:</strong> ${
                                strategyEscape(bank.bank_name || "Not configured")
                            }</p>

                            <p><strong>Account name:</strong> ${
                                strategyEscape(bank.account_name || "Not configured")
                            }</p>

                            <p><strong>Account number:</strong> ${
                                strategyEscape(bank.account_number || "Not configured")
                            }</p>
                        </div>

                        <div class="strategy-record-actions">
                            <button
                                class="secondary-button"
                                type="button"
                                id="editPaymentBankDetailsButton"
                            >
                                ${bankSetting ? "Edit Bank Details" : "Set Up Bank Details"}
                            </button>
                        </div>
                    </article>
                `;
            })()
        }

        <div class="strategy-record-list" style="margin-top: 18px;">
    ${
        strategySettings
            .filter(setting =>
                setting.key !== PUBLIC_SITE_SETTING_KEY &&
                setting.key !== PAYMENT_BANK_DETAILS_SETTING_KEY
            )
            .map(setting => `
                <article class="strategy-record">
                    <div class="strategy-record-main">
                        <div class="strategy-record-title">
                            <h4>${strategyEscape(setting.key)}</h4>

                            <span class="strategy-status ${
                                setting.is_public
                                    ? "status-active"
                                    : "status-inactive"
                            }">
                                ${setting.is_public ? "Public" : "Private"}
                            </span>
                        </div>

                        <pre class="strategy-json-preview">${strategyEscape(
                            JSON.stringify(setting.value, null, 2)
                        )}</pre>
                    </div>

                    <div class="strategy-record-actions">
                        <button
                            class="secondary-button"
                            type="button"
                            data-setting-edit="${strategyEscape(setting.key)}"
                        >
                            Edit JSON
                        </button>
                    </div>
                </article>
            `).join("")
    }
</div>
    `;

    document.getElementById("editPublicSiteSettingsButton")
        ?.addEventListener("click", () => {
            openPublicSiteSettingsModal(publicSite, publicSiteSetting);
        });

    document.getElementById("editPaymentBankDetailsButton")
        ?.addEventListener("click", () => {
            const bankSetting = strategySettings.find(
                setting => setting.key === PAYMENT_BANK_DETAILS_SETTING_KEY
            );

            openPaymentBankDetailsModal(bankSetting);
        });

    container.querySelectorAll("[data-setting-edit]").forEach(button => {
        button.addEventListener("click", () => {
            const setting = strategySettings.find(
                item => item.key === button.dataset.settingEdit
            );

            if (setting) {
                editStrategySetting(setting);
            }
        });
    });
}

function openPublicSiteSettingsModal(
    settings = DEFAULT_PUBLIC_SITE_SETTINGS,
    existingSetting = null
) {
    const modal = document.getElementById("publicSiteSettingsModal");
    const form = document.getElementById("publicSiteSettingsForm");

    if (!modal || !form) {
        strategyMessage(
            "Website Settings modal not found. Check dashboard.html.",
            true
        );
        return;
    }

    form.reset();

    document.getElementById("publicSiteBrandName").value =
        settings.brand_name || "";

    document.getElementById("publicSiteBrandSubtitle").value =
        settings.brand_subtitle || "";

    document.getElementById("publicSiteSupportUrl").value =
        settings.support_url || "";

    document.getElementById("publicSiteContactLabel").value =
        settings.contact_label || "";

    document.getElementById("publicSiteFooterName").value =
        settings.footer_name || "";

    document.getElementById("publicSiteFooterBrand").value =
        settings.footer_brand || "";

    document.getElementById("publicSiteFooterTagline").value =
        settings.footer_tagline || "";

    document.getElementById("publicSiteIsPublic").checked =
        existingSetting ? Boolean(existingSetting.is_public) : true;

    document.getElementById("publicSiteSettingsModalTitle").textContent =
        existingSetting ? "Edit Website Settings" : "Set Up Website Identity";

    modal.classList.add("active");
}

function closePublicSiteSettingsModal() {
    document.getElementById("publicSiteSettingsModal")
        ?.classList.remove("active");
}

async function savePublicSiteSettings(event) {
    event.preventDefault();

    const value = {
        brand_name: document.getElementById("publicSiteBrandName").value.trim(),
        brand_subtitle: document.getElementById("publicSiteBrandSubtitle").value.trim(),
        support_url: document.getElementById("publicSiteSupportUrl").value.trim(),
        contact_label: document.getElementById("publicSiteContactLabel").value.trim(),
        footer_name: document.getElementById("publicSiteFooterName").value.trim(),
        footer_brand: document.getElementById("publicSiteFooterBrand").value.trim(),
        footer_tagline: document.getElementById("publicSiteFooterTagline").value.trim()
    };

    const isPublic = document.getElementById("publicSiteIsPublic").checked;

    if (
        !value.brand_name ||
        !value.brand_subtitle ||
        !value.support_url ||
        !value.contact_label ||
        !value.footer_name ||
        !value.footer_brand ||
        !value.footer_tagline
    ) {
        strategyMessage("Please complete all website settings fields.", true);
        return;
    }

    let supportUrl;

    try {
        supportUrl = new URL(value.support_url);
    } catch {
        strategyMessage("Enter a valid Telegram support URL.", true);
        return;
    }

    if (
        supportUrl.protocol !== "https:" ||
        supportUrl.hostname !== "t.me"
    ) {
        strategyMessage(
            "The support link must be a valid HTTPS Telegram link.",
            true
        );
        return;
    }

    const button = document.getElementById("savePublicSiteSettingsButton");

    button.disabled = true;
    button.textContent = "Saving...";

    try {
        await strategyRequest(
            `/settings/${encodeURIComponent(PUBLIC_SITE_SETTING_KEY)}`,
            {
                method: "PUT",
                body: JSON.stringify({
                    value,
                    is_public: isPublic
                })
            }
        );

        strategyMessage("Public website settings saved successfully.");

        closePublicSiteSettingsModal();

        await loadStrategySettings();

    } catch (error) {
        console.error("Website settings save error:", error);
        strategyMessage(error.message, true);

    } finally {
        button.disabled = false;
        button.textContent = "Save Settings";
    }
}

// --------------------------------------------------
// PAYMENT BANK DETAILS MODAL
// --------------------------------------------------

function openPaymentBankDetailsModal(existingSetting = null) {
    const modal = document.getElementById("paymentBankDetailsModal");
    const form = document.getElementById("paymentBankDetailsForm");

    if (!modal || !form) {
        strategyMessage(
            "Payment Bank Details modal not found. Check dashboard.html.",
            true
        );
        return;
    }

    const bank = existingSetting?.value || {};

    form.reset();

    document.getElementById("paymentBankName").value =
        bank.bank_name || "";

    document.getElementById("paymentAccountName").value =
        bank.account_name || "";

    document.getElementById("paymentAccountNumber").value =
        bank.account_number || "";

    document.getElementById("paymentBankIsPublic").checked =
        existingSetting ? Boolean(existingSetting.is_public) : true;

    document.getElementById("paymentBankDetailsModalTitle").textContent =
        existingSetting ? "Edit Payment Bank Details" : "Set Up Payment Bank Details";

    modal.classList.add("active");
}

function closePaymentBankDetailsModal() {
    document.getElementById("paymentBankDetailsModal")
        ?.classList.remove("active");
}

async function savePaymentBankDetails(event) {
    event.preventDefault();

    const value = {
        bank_name: document.getElementById("paymentBankName").value.trim(),
        account_name: document.getElementById("paymentAccountName").value.trim(),
        account_number: document.getElementById("paymentAccountNumber").value.trim()
    };

    const isPublic = document.getElementById("paymentBankIsPublic").checked;

    if (
        !value.bank_name ||
        !value.account_name ||
        !value.account_number
    ) {
        strategyMessage("Please complete all bank details fields.", true);
        return;
    }

    const button = document.getElementById("savePaymentBankDetailsButton");

    if (!button) {
        strategyMessage("Save Bank Details button not found.", true);
        return;
    }

    button.disabled = true;
    button.textContent = "Saving...";

    try {
        await strategyRequest(
            `/settings/${encodeURIComponent(PAYMENT_BANK_DETAILS_SETTING_KEY)}`,
            {
                method: "PUT",
                body: JSON.stringify({
                    value,
                    is_public: isPublic
                })
            }
        );

        strategyMessage("Payment bank details saved successfully.");

        closePaymentBankDetailsModal();

        await loadStrategySettings();

    } catch (error) {
        console.error("Payment bank details save error:", error);
        strategyMessage(error.message, true);

    } finally {
        button.disabled = false;
        button.textContent = "Save Bank Details";
    }
}

// Existing non-public website settings continue to use the JSON editor.

async function editStrategySetting(setting) {
    const json = prompt(
        `Edit JSON value for "${setting.key}". Keep valid JSON:`,
        JSON.stringify(setting.value, null, 2)
    );

    if (json === null) {
        return;
    }

    let value;

    try {
        value = JSON.parse(json);
    } catch {
        strategyMessage("Invalid JSON. No changes were saved.", true);
        return;
    }

    const isPublic = confirm(
        "Press OK to make this setting PUBLIC.\n" +
        "Press Cancel to keep it PRIVATE."
    );

    try {
        await strategyRequest(
            `/settings/${encodeURIComponent(setting.key)}`,
            {
                method: "PUT",
                body: JSON.stringify({
                    value,
                    is_public: isPublic
                })
            }
        );

        strategyMessage("Website setting updated.");

        await loadStrategySettings();

    } catch (error) {
        strategyMessage(error.message, true);
    }
}


// --------------------------------------------------
// BOOKINGS
// --------------------------------------------------


async function loadStrategyBookings() {
    const container = document.getElementById("strategyBookingsList");

    if (!container) {
        return;
    }

    const offset =
        (strategyBookingsPage - 1) * STRATEGY_BOOKINGS_PAGE_SIZE;

    const data = await strategyRequest(
        `/bookings?offset=${offset}&limit=${STRATEGY_BOOKINGS_PAGE_SIZE}`
    );

    const bookings = strategyArray(
        data,
        ["items", "bookings", "results"]
    );

    strategyBookingsTotal = Number(data.total || 0);

    const totalPages = Math.ceil(
        strategyBookingsTotal / STRATEGY_BOOKINGS_PAGE_SIZE
    );

    if (!bookings.length) {
        container.innerHTML = strategyEmpty(
            "No strategy bookings found."
        );
        return;
    }

    const bookingCards = bookings.map((booking) => {
        const customer = booking.customer || {};

        return `
            <article class="strategy-record">

                <div class="strategy-record-main">

                    <div class="strategy-record-title">
                        <h4>${strategyEscape(
                            customer.full_name || "Unknown Customer"
                        )}</h4>

                        <span class="strategy-status">
                            ${strategyEscape(
                                booking.booking_status || "Unknown"
                            )}
                        </span>
                    </div>

                    <p>
                        <strong>Email:</strong>
                        ${strategyEscape(customer.email || "—")}
                    </p>

                    <p>
                        <strong>WhatsApp:</strong>
                        ${strategyEscape(customer.whatsapp || "—")}
                    </p>

                    <p>
                        <strong>Country:</strong>
                        ${strategyEscape(customer.country || "—")}
                    </p>

                    <div class="strategy-record-meta">

                        <span>
                            Reference:
                            ${strategyEscape(
                                booking.booking_reference || "—"
                            )}
                        </span>

                        <span>
                            Package:
                            ${strategyEscape(
                                booking.package_name || "—"
                            )}
                        </span>

                        <strong>
                            ${strategyMoney(booking.amount_ngn)}
                        </strong>

                        <span>
                            Sessions:
                            ${Number(booking.session_count || 0)}
                        </span>

                        <span>
                            Booking ID:
                            ${strategyEscape(
                                booking.booking_id ?? "—"
                            )}
                        </span>

                    </div>

                    <p>
                        <strong>Booking status:</strong>
                        ${strategyEscape(
                            booking.booking_status || "Unknown"
                        )}
                    </p>

                    <p>
                        <strong>Created:</strong>
                        ${strategyDateTime(booking.created_at)}
                    </p>

                    ${
                        customer.case_notes
                            ? `
                                <p>
                                    <strong>Case notes:</strong>
                                    ${strategyEscape(customer.case_notes)}
                                </p>
                            `
                            : ""
                    }

                </div>

            </article>
        `;
    }).join("");

    const startRecord = offset + 1;
    const endRecord = offset + bookings.length;

    let paginationHTML = "";

    if (totalPages > 1) {
        const pageButtons = Array.from(
            { length: totalPages },
            (_, index) => {
                const page = index + 1;

                return `
                    <button
                        type="button"
                        class="secondary-button"
                        data-booking-page="${page}"
                        ${page === strategyBookingsPage ? "disabled" : ""}
                        aria-current="${
                            page === strategyBookingsPage ? "page" : "false"
                        }"
                    >
                        ${page}
                    </button>
                `;
            }
        ).join("");

        paginationHTML = `
            <div class="strategy-bookings-pagination"
                 style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:20px;">

                <span>
                    Showing ${startRecord}–${endRecord}
                    of ${strategyBookingsTotal} bookings
                </span>

                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">

                    <button
                        type="button"
                        class="secondary-button"
                        data-booking-page="${strategyBookingsPage - 1}"
                        ${strategyBookingsPage === 1 ? "disabled" : ""}
                    >
                        Previous
                    </button>

                    ${pageButtons}

                    <button
                        type="button"
                        class="secondary-button"
                        data-booking-page="${strategyBookingsPage + 1}"
                        ${strategyBookingsPage === totalPages ? "disabled" : ""}
                    >
                        Next
                    </button>

                </div>
            </div>
        `;
    } else {
        paginationHTML = `
            <div style="margin-top:20px;">
                Showing ${startRecord}–${endRecord}
                of ${strategyBookingsTotal} bookings
            </div>
        `;
    }

    container.innerHTML = bookingCards + paginationHTML;

    container.querySelectorAll("[data-booking-page]").forEach((button) => {
        button.addEventListener("click", async () => {
            const requestedPage = Number(button.dataset.bookingPage);

            if (
                !Number.isInteger(requestedPage) ||
                requestedPage < 1 ||
                requestedPage > totalPages ||
                requestedPage === strategyBookingsPage
            ) {
                return;
            }

            strategyBookingsPage = requestedPage;

            try {
                await loadStrategyBookings();
            } catch (error) {
                console.error("Booking pagination error:", error);
                strategyMessage(error.message, true);
            }
        });
    });
}


// --------------------------------------------------
// EVENT HANDLERS
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {

    // Add consultation package

    document.getElementById("addStrategyServiceButton")
        ?.addEventListener("click", async () => {
            try {
                openStrategyPackageModal();
            } catch (error) {
                console.error("Package creation error:", error);
                strategyMessage(error.message, true);
            }
        });

    document.getElementById("strategyPackageForm")
        ?.addEventListener("submit", saveStrategyPackage);

    document.getElementById("closeStrategyPackageModal")
        ?.addEventListener("click", closeStrategyPackageModal);

    document.getElementById("cancelStrategyPackageModal")
        ?.addEventListener("click", closeStrategyPackageModal);

    // Add website content section

    document.getElementById("addStrategyContentButton")
        ?.addEventListener("click", async () => {
            try {
                await createStrategySection();
            } catch (error) {
                console.error("Website content creation error:", error);
                strategyMessage(error.message, true);
            }
        });

    document.getElementById("strategyContentForm")
        ?.addEventListener("submit", saveStrategyContent);

    document.getElementById("closeStrategyContentModal")
        ?.addEventListener("click", closeStrategyContentModal);

    document.getElementById("cancelStrategyContentModal")
        ?.addEventListener("click", closeStrategyContentModal);


    // Website Settings modal

    document.getElementById("publicSiteSettingsForm")
        ?.addEventListener("submit", savePublicSiteSettings);

    document.getElementById("closePublicSiteSettingsModal")
        ?.addEventListener("click", closePublicSiteSettingsModal);

    document.getElementById("cancelPublicSiteSettingsModal")
        ?.addEventListener("click", closePublicSiteSettingsModal);

    document.getElementById("publicSiteSettingsModal")
        ?.addEventListener("click", (event) => {
            if (event.target.id === "publicSiteSettingsModal") {
                closePublicSiteSettingsModal();
            }
        });

    // Payment Bank Details modal

    document.getElementById("paymentBankDetailsForm")
        ?.addEventListener("submit", savePaymentBankDetails);

    document.getElementById("closePaymentBankDetailsModal")
        ?.addEventListener("click", closePaymentBankDetailsModal);

    document.getElementById("cancelPaymentBankDetailsModal")
        ?.addEventListener("click", closePaymentBankDetailsModal);

    document.getElementById("paymentBankDetailsModal")
        ?.addEventListener("click", (event) => {
            if (event.target.id === "paymentBankDetailsModal") {
                closePaymentBankDetailsModal();
            }
        });


    document.getElementById("strategyContentModal")
        ?.addEventListener("click", (event) => {
            if (event.target.id === "strategyContentModal") {
                closeStrategyContentModal();
            }
        });

    // Refresh all strategy website data

    document.getElementById("refreshStrategyButton")
        ?.addEventListener("click", async () => {
            await loadStrategyDashboard();
        });

    // Refresh bookings

    document.getElementById("refreshStrategyBookingsButton")
        ?.addEventListener("click", async () => {
            try {
                await loadStrategyBookings();
                strategyMessage("Bookings refreshed.");
            } catch (error) {
                console.error("Booking refresh error:", error);
                strategyMessage(error.message, true);
            }
        });

    // Strategy tabs

    document.querySelectorAll("[data-strategy-tab]").forEach((button) => {

        button.addEventListener("click", async () => {

            const tab = button.dataset.strategyTab;

            document.querySelectorAll("[data-strategy-tab]").forEach(item => {
                item.classList.toggle("active", item === button);
            });

            document.querySelectorAll(
                "#strategy .strategy-panel"
            ).forEach(panel => {
                panel.classList.toggle(
                    "active",
                    panel.id === `strategy-${tab}`
                );
            });

            try {
                if (tab === "packages") {
                    await loadStrategyServices();
                }

                if (tab === "content") {
                    await loadStrategySections();
                }

                if (tab === "settings") {
                    await loadStrategySettings();
                }

                if (tab === "bookings") {
                    await loadStrategyBookings();
                }

            } catch (error) {
                console.error(
                    `Strategy ${tab} loading error:`,
                    error
                );

                strategyMessage(error.message, true);
            }
        });

    });

});