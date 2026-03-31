/**
 * Main application logic — password auth, data fetching, auto-refresh.
 * Simple shared-password auth via Authorization: Bearer <password> header.
 */

let CONFIG = {};
let dashboardPassword = null;
let currentOrg = "all";
let refreshTimer = null;

// ---- Init ----

async function init() {
    const resp = await fetch("config.json");
    CONFIG = await resp.json();

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

    // Org filter buttons
    document.querySelectorAll(".org-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".org-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentOrg = btn.dataset.org;
            fetchAndRender();
        });
    });

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
        const [stats, appData] = await Promise.all([
            apiFetch(`/api/stats?org=${currentOrg}`),
            apiFetch(`/api/applications?org=${currentOrg}`),
        ]);

        updateCards(stats);
        renderCharts(stats);
        renderTable(appData.applications || []);

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
    document.getElementById("card-total-detail").textContent =
        `CSU: ${total.csu || 0} | CCC: ${total.ccc || 0}`;
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

function renderTable(applications) {
    const tbody = document.getElementById("applications-tbody");
    tbody.innerHTML = "";

    for (const app of applications.slice(0, 100)) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${esc(app.firstName || "")} ${esc(app.lastName || "")}</td>
            <td>${esc(app.email || "")}</td>
            <td><span class="org-tag">${esc(app.org || "")}</span></td>
            <td>${esc(app.institution || "")}</td>
            <td>${esc(app.majorCategory || "")}</td>
            <td>${app.csBackground ? "Yes" : "No"}</td>
            <td>${app.isOfAge ? "Yes" : "No"}</td>
            <td>${esc((app.submittedAt || "").slice(0, 10))}</td>
        `;
        tbody.appendChild(tr);
    }
}

function esc(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}

// ---- Boot ----
document.addEventListener("DOMContentLoaded", init);
