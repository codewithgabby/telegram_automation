
"use strict";

const FAQ_API_URL = "https://telegram-automation-nlq9.onrender.com/admin/faqs";

const FAQ_ACCESS_TOKEN_KEY = "admin_access_token";

document.addEventListener("DOMContentLoaded", () => {

    const faqList = document.getElementById("faqList");
    const faqForm = document.getElementById("faqForm");
    const faqModal = document.getElementById("faqModal");
    const faqSearch = document.getElementById("faqSearch");

    if (!faqList || !faqForm) return;

    let faqs = [];

    // =================================
    // API REQUEST HELPER
    // =================================

    async function apiRequest(endpoint, options = {}) {

        const accessToken = sessionStorage.getItem(FAQ_ACCESS_TOKEN_KEY);

        if (!accessToken) {
            window.location.replace("index.html");
            throw new Error("Authentication required. Please sign in again.");
        }

        const headers = {
            ...options.headers,
            "Authorization": `Bearer ${accessToken}`
        };

        if (options.body) {
            headers["Content-Type"] = "application/json";
        }

        const response = await fetch(`${FAQ_API_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {

            sessionStorage.removeItem(FAQ_ACCESS_TOKEN_KEY);

            window.location.replace("index.html");

            throw new Error("Your session has expired. Please sign in again.");
        }

        if (response.status === 204) {
            return null;
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.detail || "Something went wrong. Please try again."
            );
        }

        return data;
    }


    // =================================
    // LOAD FAQs
    // =================================

    async function loadFaqs() {

        faqList.textContent = "Loading FAQs...";

        try {
            faqs = await apiRequest("");

            updateStatistics();
            renderFaqs(faqs);

        } catch (error) {
            console.error("FAQ loading error:", error);

            faqList.textContent = error.message;
        }
    }


    // =================================
    // UPDATE STATISTICS
    // =================================

    function updateStatistics() {

        const total = faqs.length;
        const active = faqs.filter(faq => faq.is_active).length;
        const inactive = total - active;

        document.getElementById("totalFaqs").textContent = total;
        document.getElementById("activeFaqs").textContent = active;
        document.getElementById("inactiveFaqs").textContent = inactive;
    }


    // =================================
    // RENDER FAQs
    // =================================

    function renderFaqs(records) {

        faqList.replaceChildren();

        if (records.length === 0) {

            const emptyState = document.createElement("div");
            emptyState.className = "empty-state";

            const heading = document.createElement("h3");
            heading.textContent = "No FAQs found";

            const message = document.createElement("p");
            message.textContent = "Add a new FAQ or try another search.";

            emptyState.append(heading, message);
            faqList.appendChild(emptyState);

            return;
        }

        records.forEach(faq => {

            const card = document.createElement("article");
            card.className = "faq-item";

            const content = document.createElement("div");
            content.className = "faq-item-content";

            const title = document.createElement("h3");
            title.textContent = faq.topic;

            const keywords = document.createElement("p");
            keywords.textContent = `Keywords: ${faq.keywords.join(", ")}`;

            const link = document.createElement("a");
            link.href = faq.message_link;
            link.textContent = "View Telegram discussion";
            link.target = "_blank";
            link.rel = "noopener noreferrer";

            const status = document.createElement("span");
            status.className = faq.is_active
                ? "faq-status active"
                : "faq-status inactive";

            status.textContent = faq.is_active ? "Active" : "Inactive";

            content.append(title, keywords, link);

            const actions = document.createElement("div");
            actions.className = "faq-actions";

            const editButton = createActionButton("Edit", "edit");
            editButton.addEventListener("click", () => editFaq(faq));

            const toggleButton = createActionButton(
                faq.is_active ? "Deactivate" : "Activate",
                "toggle"
            );

            toggleButton.addEventListener("click", () => toggleFaq(faq));

            const deleteButton = createActionButton("Delete", "delete");
            deleteButton.addEventListener("click", () => deleteFaq(faq));

            actions.append(status, editButton, toggleButton, deleteButton);

            card.append(content, actions);
            faqList.appendChild(card);
        });
    }


    // =================================
    // CREATE ACTION BUTTONS
    // =================================

    function createActionButton(label, type) {

        const button = document.createElement("button");

        button.type = "button";
        button.className = `faq-action-button ${type}`;
        button.textContent = label;

        return button;
    }


    // =================================
    // SEARCH FAQs
    // =================================

    faqSearch?.addEventListener("input", () => {

        const searchTerm = faqSearch.value.toLowerCase().trim();

        const filteredFaqs = faqs.filter(faq => {

            const topicMatches = faq.topic.toLowerCase().includes(searchTerm);

            const keywordMatches = faq.keywords.some(keyword =>
                keyword.toLowerCase().includes(searchTerm)
            );

            return topicMatches || keywordMatches;
        });

        renderFaqs(filteredFaqs);
    });


    // =================================
    // OPEN FAQ MODAL
    // =================================

    function openFaqModal() {
        faqForm.reset();

        document.getElementById("faqId").value = "";

        document.getElementById("modalTitle").textContent = "Add New FAQ";

        document.getElementById("saveFaqButton").textContent = "Save FAQ";

        faqModal.classList.add("show");
    }


    function closeFaqModal() {
        faqModal.classList.remove("show");
    }


    // =================================
    // EDIT FAQ
    // =================================

    function editFaq(faq) {

        document.getElementById("faqId").value = faq.id;

        document.getElementById("faqTopic").value = faq.topic;

        document.getElementById("faqKeywords").value =
            faq.keywords.join(", ");

        document.getElementById("faqLink").value = faq.message_link;

        document.getElementById("modalTitle").textContent = "Edit FAQ";

        document.getElementById("saveFaqButton").textContent = "Update FAQ";

        faqModal.classList.add("show");
    }


    // =================================
    // CREATE OR UPDATE FAQ
    // =================================

    faqForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        const faqId = document.getElementById("faqId").value;

        const topic = document.getElementById("faqTopic").value.trim();

        const keywords = document.getElementById("faqKeywords")
            .value
            .split(",")
            .map(keyword => keyword.trim())
            .filter(Boolean);

        const messageLink = document.getElementById("faqLink").value.trim();

        if (keywords.length === 0) {
            alert("Please enter at least one keyword.");
            return;
        }

        const faqData = {
            topic,
            keywords,
            message_link: messageLink
        };

        const saveButton = document.getElementById("saveFaqButton");

        saveButton.disabled = true;
        saveButton.textContent = "Saving...";

        try {

            if (faqId) {

                await apiRequest(`/${faqId}`, {
                    method: "PATCH",
                    body: JSON.stringify(faqData)
                });

            } else {

                await apiRequest("", {
                    method: "POST",
                    body: JSON.stringify(faqData)
                });
            }

            closeFaqModal();
            faqSearch.value = "";

            await loadFaqs();

            alert(faqId ? "FAQ updated successfully." : "FAQ created successfully.");

        } catch (error) {

            console.error("FAQ save error:", error);
            alert(error.message);

        } finally {

            saveButton.disabled = false;
            saveButton.textContent = faqId ? "Update FAQ" : "Save FAQ";
        }
    });


    // =================================
    // ACTIVATE / DEACTIVATE FAQ
    // =================================

    async function toggleFaq(faq) {

        const action = faq.is_active ? "deactivate" : "activate";

        if (!confirm(`Are you sure you want to ${action} this FAQ?`)) {
            return;
        }

        try {

            if (faq.is_active) {

                await apiRequest(`/${faq.id}/deactivate`, {
                    method: "PATCH"
                });

            } else {

                await apiRequest(`/${faq.id}`, {
                    method: "PATCH",
                    body: JSON.stringify({
                        is_active: true
                    })
                });
            }

            await loadFaqs();

        } catch (error) {

            console.error("FAQ status error:", error);
            alert(error.message);
        }
    }


    // =================================
    // DELETE FAQ
    // =================================

    async function deleteFaq(faq) {

        if (!confirm(`Are you sure you want to permanently delete "${faq.topic}"?`)) {
            return;
        }

        try {

            await apiRequest(`/${faq.id}`, {
                method: "DELETE"
            });

            await loadFaqs();

        } catch (error) {

            console.error("FAQ deletion error:", error);
            alert(error.message);
        }
    }


    // =================================
    // INITIAL LOAD AFTER AUTHENTICATION
    // =================================

    document.addEventListener("adminAuthenticated", () => {
        loadFaqs();
    });

});
