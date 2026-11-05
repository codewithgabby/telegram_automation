
"use strict";

// =============================================
// CONFIGURATION
// =============================================

const API_BASE_URL = "https://telegram-automation-nlq9.onrender.com";

const ACCESS_TOKEN_KEY = "admin_access_token";

const loginForm = document.getElementById("loginForm");


// =============================================
// ACCESS TOKEN MANAGEMENT
// =============================================

function getAccessToken() {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

function clearAccessToken() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}


// =============================================
// ADMIN LOGIN
// =============================================

if (loginForm) {

    const loginButton = document.getElementById("loginButton");
    const loginError = document.getElementById("loginError");

    loginForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        loginError.textContent = "";

        const username = document
            .getElementById("username")
            .value
            .trim();

        const password = document
            .getElementById("password")
            .value;

        if (!username || !password) {
            loginError.textContent =
                "Please enter your username and password.";
            return;
        }

        loginButton.disabled = true;
        loginButton.textContent = "Signing in...";

        try {

            const response = await fetch(
                `${API_BASE_URL}/admin/auth/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        username,
                        password
                    })
                }
            );

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "Login failed. Please check your credentials."
                );
            }

            // Validate the access token returned by the backend.

            if (!data.access_token) {
                throw new Error(
                    "Login response did not include an access token."
                );
            }

            // Store the access token for authenticated requests.

            sessionStorage.setItem(
                ACCESS_TOKEN_KEY,
                data.access_token
            );

            // Proceed to the dashboard.

            window.location.replace("dashboard.html");

        } catch (error) {

            console.error("Login error:", error);

            loginError.textContent =
                error.message ||
                "Unable to connect to the server. Please try again.";

        } finally {

            loginButton.disabled = false;
            loginButton.textContent = "Sign In";

        }

    });

}


// =============================================
// DASHBOARD SESSION VERIFICATION
// =============================================

if (!loginForm) {

    async function verifyAdminSession() {

        const accessToken = getAccessToken();

        if (!accessToken) {
            window.location.replace("index.html");
            return;
        }

        try {

            const response = await fetch(
                `${API_BASE_URL}/admin/auth/me`,
                {
                    method: "GET",

                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                }
            );

            if (!response.ok) {

                clearAccessToken();

                window.location.replace("index.html");

                return;
            }

            // Authentication succeeded.
            // Reveal the dashboard and notify faqs.js.

            document.body.classList.remove("auth-pending");

            document.dispatchEvent(
                new Event("adminAuthenticated")
            );

        } catch (error) {

            console.error(
                "Session verification failed:",
                error
            );

            window.location.replace("index.html");

        }

    }


    // Wait until the dashboard document is ready.

    document.addEventListener(
        "DOMContentLoaded",
        verifyAdminSession
    );


    // =============================================
    // ADMIN LOGOUT
    // =============================================

    const logoutButton = document.getElementById("logoutButton");

    if (logoutButton) {

        logoutButton.addEventListener("click", async () => {

            const confirmed = confirm(
                "Are you sure you want to sign out?"
            );

            if (!confirmed) {
                return;
            }

            const accessToken = getAccessToken();

            if (!accessToken) {

                clearAccessToken();

                window.location.replace("index.html");

                return;
            }

            logoutButton.disabled = true;
            logoutButton.textContent = "Signing out...";

            try {

                const response = await fetch(
                    `${API_BASE_URL}/admin/auth/logout`,
                    {
                        method: "POST",

                        headers: {
                            "Authorization": `Bearer ${accessToken}`
                        }
                    }
                );

                if (!response.ok) {

                    const data = await response
                        .json()
                        .catch(() => ({}));

                    throw new Error(
                        data.detail ||
                        "Unable to sign out. Please try again."
                    );
                }

                // Clear the stored access token.

                clearAccessToken();

                // Return to login page.

                window.location.replace("index.html");

            } catch (error) {

                console.error("Logout error:", error);

                alert(error.message);

                logoutButton.disabled = false;
                logoutButton.textContent = "↪ Sign out";

            }

        });

    }

}
