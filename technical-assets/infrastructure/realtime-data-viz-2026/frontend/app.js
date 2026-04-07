/**
 * Main application logic — password auth, data fetching, auto-refresh.
 * Simple shared-password auth via Authorization: Bearer <password> header.
 */

let CONFIG = {};
let dashboardPassword = null;
let currentOrg = null;
let refreshTimer = null;

// ---- Init ----

async function init() {
    const resp = await fetch("config.json");
    CONFIG = await resp.json();
    currentOrg = CONFIG.org || "all";
    const orgLabel = currentOrg.toUpperCase();
    const siteTitle = `${orgLabel} AI Summer Camp 2026`;
    document.title = siteTitle + " - Admin Dashboard";
    document.querySelector("#login-screen h1").textContent = siteTitle;
    document.querySelector("#dashboard .topbar h1").textContent = siteTitle;

    // Check for stored session
    const saved = sessionStorage.getItem("dashPassword");
    if (saved) {
        dashboardPassword = saved;
        // Verify it still works
        try {
            await apiFetch("/api/stats?org=all");
            showDashboard();
            return;
        } catch (_) {
            sessionStorage.removeItem("dashPassword");
            dashboardPassword = null;
        }
    }

    setupLoginForm();
}

// ---- Auth ----

function setupLoginForm() {
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const password = document.getElementById("password").value;
        const errorEl = document.getElementById("login-error");
        const btn = document.getElementById("login-btn");

        errorEl.hidden = true;
        btn.textContent = "Signing in...";
        btn.disabled = true;

        try {
            // Test the password against the API
            dashboardPassword = password;
            await apiFetch("/api/stats?org=all");

            // Success — store and show dashboard
            sessionStorage.setItem("dashPassword", password);
            showDashboard();
        } catch (err) {
            dashboardPassword = null;
            errorEl.textContent = "Invalid password";
            errorEl.hidden = false;
        } finally {
            btn.textContent = "Sign In";
            btn.disabled = false;
        }
    });
}

function logout() {
    dashboardPassword = null;
    sessionStorage.removeItem("dashPassword");
    if (refreshTimer) clearInterval(refreshTimer);
    document.getElementById("dashboard").hidden = true;
    document.getElementById("login-screen").hidden = false;
}

// ---- Dashboard ----

function showDashboard() {
    document.getElementById("login-screen").hidden = true;
    document.getElementById("dashboard").hidden = false;

    // Hide org-specific charts that don't belong to this site
    if (currentOrg === "csu" || currentOrg === "ccc") {
        document.querySelectorAll(".chart-box[data-org]").forEach((el) => {
            el.hidden = el.dataset.org !== currentOrg;
        });
    }

    document.getElementById("logout-btn").addEventListener("click", logout);

    // Initial fetch + auto-refresh
    fetchAndRender();
    refreshTimer = setInterval(fetchAndRender, CONFIG.refreshIntervalMs || 30000);
}

async function apiFetch(path) {
    const url = `${CONFIG.apiBaseUrl}${path}`;
    const res = await fetch(url, {
        headers: { Authorization: `Bearer ${dashboardPassword}` },
    });
    if (res.status === 401) {
        logout();
        throw new Error("Unauthorized");
    }
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

async function fetchAndRender() {
    const dot = document.getElementById("refresh-indicator");
    dot.classList.add("loading");

    try {
        const [stats] = await Promise.all([
            apiFetch(`/api/stats?org=${currentOrg}`),
        ]);

        updateCards(stats);
        renderCharts(stats);

        document.getElementById("last-updated").textContent =
            `Updated ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        console.error("Fetch error:", err);
    } finally {
        dot.classList.remove("loading");
    }
}

function updateCards(stats) {
    const total = stats.totalApplicants || {};
    document.getElementById("card-total").textContent = total.all || 0;
    document.getElementById("card-total-detail").textContent = "";
    document.getElementById("card-qualified").textContent = stats.qualifiedApplicants || 0;
    document.getElementById("card-institutions").textContent = stats.institutionsCount || 0;

    const quiz = stats.quiz || {};
    document.getElementById("card-quiz-submissions").textContent = quiz.totalQuizTakers || 0;

    const xref = stats.crossReference || {};
    const quizPct = total.all
        ? Math.round(((xref.appliedAndQuiz || 0) / total.all) * 100)
        : 0;
    document.getElementById("card-quiz-completion").textContent = `${quizPct}%`;

    document.getElementById("card-avg-score").textContent =
        quiz.averageScore ? `${quiz.averageScore}%` : "--";
}

// ---- Boot ----
document.addEventListener("DOMContentLoaded", init);
