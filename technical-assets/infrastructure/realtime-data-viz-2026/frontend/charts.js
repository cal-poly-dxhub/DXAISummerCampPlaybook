/**
 * Chart manager — creates and updates Chart.js instances.
 * Uses chart.update() for smooth transitions instead of destroy/recreate.
 */

const COLORS = [
    "#2196f3", "#f44336", "#4caf50", "#ff9800", "#9c27b0",
    "#00bcd4", "#ff5722", "#607d8b", "#e91e63", "#3f51b5",
    "#009688", "#ffc107", "#795548", "#8bc34a", "#03a9f4",
    "#cddc39", "#673ab7", "#ffeb3b", "#ff6f00", "#1b5e20",
];

const COLORS_ALPHA = COLORS.map(c => c + "cc");

const charts = {};

function getOrCreate(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (charts[canvasId]) {
        return charts[canvasId];
    }

    charts[canvasId] = new Chart(ctx, config);
    return charts[canvasId];
}

function updateBarChart(canvasId, labels, data, label, horizontal = false) {
    const existing = charts[canvasId];
    const config = {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: COLORS_ALPHA.slice(0, data.length),
                borderColor: COLORS.slice(0, data.length),
                borderWidth: 1,
            }],
        },
        options: {
            indexAxis: horizontal ? "y" : "x",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                [horizontal ? "x" : "y"]: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    };

    if (existing) {
        existing.data.labels = labels;
        existing.data.datasets[0].data = data;
        existing.data.datasets[0].backgroundColor = COLORS_ALPHA.slice(0, data.length);
        existing.data.datasets[0].borderColor = COLORS.slice(0, data.length);
        existing.update();
    } else {
        getOrCreate(canvasId, config);
    }
}

function updateDoughnutChart(canvasId, labels, data) {
    const existing = charts[canvasId];
    const config = {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: COLORS_ALPHA.slice(0, data.length),
                borderColor: COLORS.slice(0, data.length),
                borderWidth: 1,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "right", labels: { boxWidth: 12, font: { size: 11 } } },
            },
        },
    };

    if (existing) {
        existing.data.labels = labels;
        existing.data.datasets[0].data = data;
        existing.data.datasets[0].backgroundColor = COLORS_ALPHA.slice(0, data.length);
        existing.data.datasets[0].borderColor = COLORS.slice(0, data.length);
        existing.update();
    } else {
        getOrCreate(canvasId, config);
    }
}

function updateLineChart(canvasId, labels, data, label) {
    const existing = charts[canvasId];
    const config = {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: "#2196f3",
                backgroundColor: "rgba(33, 150, 243, 0.1)",
                fill: true,
                tension: 0.3,
                pointRadius: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    };

    if (existing) {
        existing.data.labels = labels;
        existing.data.datasets[0].data = data;
        existing.update();
    } else {
        getOrCreate(canvasId, config);
    }
}

function setChartAvg(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = `Average: ${value || 0}`;
}

function weightedAvg(entries) {
    let total = 0, count = 0;
    for (const [label, cnt] of entries) {
        const num = parseFloat(label);
        if (!isNaN(num) && cnt) { total += num * cnt; count += cnt; }
    }
    return count ? (total / count).toFixed(1) : 0;
}

/**
 * Render all dashboard charts from stats data.
 */
function renderCharts(stats) {
    // Application trend
    const trend = stats.applicationTrend || [];
    updateLineChart(
        "chart-trend",
        trend.map(t => t.date),
        trend.map(t => t.count),
        "Applications"
    );

    // Institution (horizontal bar, top 15)
    const instEntries = Object.entries(stats.byInstitution || {}).slice(0, 15);
    updateBarChart(
        "chart-institution",
        instEntries.map(e => e[0]),
        instEntries.map(e => e[1]),
        "Applicants",
        true
    );

    // Major categories (doughnut)
    const majorEntries = Object.entries(stats.byMajorCategory || {});
    updateDoughnutChart(
        "chart-major",
        majorEntries.map(e => e[0]),
        majorEntries.map(e => e[1])
    );

    // CS/CPE/SE vs Other majors (pie)
    const csSplit = stats.csMajorSplit || {};
    updateDoughnutChart(
        "chart-cs-major",
        ["Computing Majors", "Other Majors"],
        [csSplit["Computing Majors"] || 0, csSplit["Other Majors"] || 0]
    );

    // Years of instruction by org
    const yearsLabels = ["1", "2", "3", "4 (or more)"];
    const yearsByOrg = stats.yearsByOrg || {};

    const csuYears = yearsByOrg.csu || {};
    updateBarChart(
        "chart-years-csu",
        yearsLabels,
        yearsLabels.map(k => csuYears[k] || 0),
        "CSU Applicants"
    );
    setChartAvg("avg-years-csu", weightedAvg(Object.entries(csuYears)));

    const cccYears = yearsByOrg.ccc || {};
    updateBarChart(
        "chart-years-ccc",
        yearsLabels,
        yearsLabels.map(k => cccYears[k] || 0),
        "CCC Applicants"
    );
    setChartAvg("avg-years-ccc", weightedAvg(Object.entries(cccYears)));

    // Cross-reference (doughnut)
    const xref = stats.crossReference || {};
    updateDoughnutChart(
        "chart-crossref",
        ["Applied + Quiz", "Applied Only", "Quiz Only"],
        [xref.appliedAndQuiz || 0, xref.appliedOnly || 0, xref.quizOnly || 0]
    );

    // Quiz score distribution (bar)
    const quiz = stats.quiz || {};
    const scoreOrder = ["0-20%", "21-40%", "41-60%", "61-80%", "81-100%"];
    const scoreDist = quiz.scoreDistribution || {};
    updateBarChart(
        "chart-scores",
        scoreOrder,
        scoreOrder.map(k => scoreDist[k] || 0),
        "Quiz Takers"
    );
    setChartAvg("avg-scores", quiz.averageScore || 0);

    // Quiz attempts (bar)
    const attemptEntries = Object.entries(quiz.attemptDistribution || {});
    updateBarChart(
        "chart-attempts",
        attemptEntries.map(e => e[0]),
        attemptEntries.map(e => e[1]),
        "Quiz Takers"
    );
    setChartAvg("avg-attempts", weightedAvg(attemptEntries));

    // Technical experience charts (application form, 1-5 ratings)
    const techExp = stats.technicalExperience || {};
    const ratingLabels = ["1", "2", "3", "4", "5"];

    const aiExp = techExp.aiExperience || {};
    updateBarChart(
        "chart-app-ai-exp",
        ratingLabels,
        ratingLabels.map(k => aiExp[k] || 0),
        "Applicants"
    );
    setChartAvg("avg-app-ai-exp", techExp.avgAiExperience);

    const cloudExp = techExp.cloudExperience || {};
    updateBarChart(
        "chart-app-cloud-exp",
        ratingLabels,
        ratingLabels.map(k => cloudExp[k] || 0),
        "Applicants"
    );
    setChartAvg("avg-app-cloud-exp", techExp.avgCloudExperience);

    const assistantExp = techExp.aiAssistantExperience || {};
    updateBarChart(
        "chart-app-assistant-exp",
        ratingLabels,
        ratingLabels.map(k => assistantExp[k] || 0),
        "Applicants"
    );
    setChartAvg("avg-app-assistant-exp", techExp.avgAiAssistantExperience);

    // Quiz technical ability (1-5 from quiz section 2)
    const quizTech = quiz.techAbility || {};
    updateBarChart(
        "chart-quiz-tech",
        ratingLabels,
        ratingLabels.map(k => quizTech[k] || 0),
        "Quiz Takers"
    );
    setChartAvg("avg-quiz-tech", quiz.avgTechAbility);

    // Avg technical experience by institution (horizontal bar)
    const techByInst = Object.entries(techExp.byInstitution || {}).slice(0, 20);
    updateBarChart(
        "chart-tech-by-institution",
        techByInst.map(e => e[0]),
        techByInst.map(e => e[1]),
        "Avg Rating (1-5)",
        true
    );
}
