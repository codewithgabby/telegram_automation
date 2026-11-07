
document.addEventListener("DOMContentLoaded", () => {

    // MOBILE SIDEBAR

    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");

    if (sidebar && menuToggle) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }

    // FAQ MODAL

    const faqModal = document.getElementById("faqModal");
    const addFaqButton = document.getElementById("addFaqButton");
    const closeModalButton = document.getElementById("closeModalButton");
    const cancelFaqButton = document.getElementById("cancelFaqButton");
    const faqForm = document.getElementById("faqForm");
    const modalTitle = document.getElementById("modalTitle");

    function openFaqModal() {
        if (!faqModal || !faqForm) return;

        faqForm.reset();
        document.getElementById("faqId").value = "";
        modalTitle.textContent = "Add New FAQ";

        faqModal.classList.add("show");
    }

    function closeFaqModal() {
        faqModal?.classList.remove("show");
    }

    addFaqButton?.addEventListener("click", openFaqModal);
    closeModalButton?.addEventListener("click", closeFaqModal);
    cancelFaqButton?.addEventListener("click", closeFaqModal);

    faqModal?.addEventListener("click", (event) => {
        if (event.target === faqModal) {
            closeFaqModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeFaqModal();
            sidebar?.classList.remove("open");
        }
    });

    // SIDEBAR NAVIGATION

    const navLinks = document.querySelectorAll(".nav-link");
    const dashboardSections = document.querySelectorAll(".dashboard-section");

    function showDashboardSection(targetId) {

        const targetSection = document.getElementById(targetId);

        if (!targetSection || !targetSection.classList.contains("dashboard-section")) {
            targetId = "overview";
        }

        dashboardSections.forEach((section) => {
            section.classList.remove("active");
        });

        document.getElementById(targetId).classList.add("active");

        navLinks.forEach((link) => {
            link.classList.toggle(
                "active",
                link.getAttribute("href") === `#${targetId}`
            );
        });

        // Load contacts when the Client Engagement page is opened.
        if (targetId === "contacts" && typeof loadContacts === "function") {
            loadContacts();
        }
    }

    navLinks.forEach((link) => {

        link.addEventListener("click", (event) => {

            event.preventDefault();

            const targetId = link.getAttribute("href").substring(1);

            showDashboardSection(targetId);

            window.location.hash = targetId;

            sidebar?.classList.remove("open");
        });

    });

    const initialSection = window.location.hash.substring(1);

    showDashboardSection(initialSection || "overview");

    window.addEventListener("hashchange", () => {

        const targetId = window.location.hash.substring(1);

        showDashboardSection(targetId || "overview");

    });

});
