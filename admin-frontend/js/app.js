
document.addEventListener("DOMContentLoaded", () => {

    // ================================
    // MOBILE SIDEBAR
    // ================================

    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");

    if (sidebar && menuToggle) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }


    // ================================
    // FAQ MODAL
    // ================================

    const faqModal = document.getElementById("faqModal");
    const addFaqButton = document.getElementById("addFaqButton");
    const closeModalButton = document.getElementById("closeModalButton");
    const cancelFaqButton = document.getElementById("cancelFaqButton");
    const faqForm = document.getElementById("faqForm");
    const modalTitle = document.getElementById("modalTitle");


    function openFaqModal() {
        if (!faqModal) return;

        faqForm.reset();

        document.getElementById("faqId").value = "";

        modalTitle.textContent = "Add New FAQ";

        faqModal.classList.add("show");
    }


    function closeFaqModal() {
        if (!faqModal) return;

        faqModal.classList.remove("show");
    }


    if (addFaqButton) {
        addFaqButton.addEventListener("click", openFaqModal);
    }

    if (closeModalButton) {
        closeModalButton.addEventListener("click", closeFaqModal);
    }

    if (cancelFaqButton) {
        cancelFaqButton.addEventListener("click", closeFaqModal);
    }


    // Close modal when clicking outside the modal card.

    if (faqModal) {
        faqModal.addEventListener("click", (event) => {
            if (event.target === faqModal) {
                closeFaqModal();
            }
        });
    }


    // Close modal with Escape key.

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeFaqModal();
            sidebar?.classList.remove("open");
        }
    });


    // ================================
// SIDEBAR NAVIGATION
// ================================

const navLinks = document.querySelectorAll(".nav-link");
const dashboardSections = document.querySelectorAll(".dashboard-section");

function showDashboardSection(targetId) {

    const targetSection = document.getElementById(targetId);

    // Only allow valid dashboard sections.
    if (!targetSection || !targetSection.classList.contains("dashboard-section")) {
        targetId = "overview";
    }

    // Hide all sections.
    dashboardSections.forEach((section) => {
        section.classList.remove("active");
    });

    // Display selected section.
    document.getElementById(targetId).classList.add("active");

    // Update sidebar navigation.
    navLinks.forEach((link) => {
        link.classList.toggle(
            "active",
            link.getAttribute("href") === `#${targetId}`
        );
    });
}

// Handle sidebar clicks.
navLinks.forEach((link) => {

    link.addEventListener("click", (event) => {

        event.preventDefault();

        const targetId = link.getAttribute("href").substring(1);

        showDashboardSection(targetId);

        // Update browser URL.
        window.location.hash = targetId;

        // Close mobile sidebar.
        sidebar?.classList.remove("open");

    });

});

// Restore selected section when the page loads.
const initialSection = window.location.hash.substring(1);

showDashboardSection(initialSection || "overview");

// Handle browser back and forward navigation.
window.addEventListener("hashchange", () => {

    const targetId = window.location.hash.substring(1);

    showDashboardSection(targetId || "overview");

});

});
