/**********************************************************************
 * AIStockX
 * comparison.js
 *
 * Production Version
 *********************************************************************/

'use strict';

/**********************************************************************
 * Global State
 *********************************************************************/

let comparisonData = null;

let radarChart = null;

let metricsChart = null;


/**********************************************************************
 * DOM Ready
 *********************************************************************/

document.addEventListener("DOMContentLoaded", () => {

    initComparisonPage();

});


/**********************************************************************
 * Initialize Page
 *********************************************************************/

function initComparisonPage() {

    showEmpty();

}


/**********************************************************************
 * Load Comparison
 *********************************************************************/

async function loadComparison() {

    const input = document.getElementById("compSymbolInput");

    if (!input) return;

    const symbol = input.value.trim().toUpperCase();

    if (!symbol) {

        alert("Please enter a stock symbol.");

        return;

    }

    try {

        showLoading();

        const response =
            await predictionsApi.compareModels(symbol);

        comparisonData = response.data;

        showContent();

        renderComparison();

    }

    catch (error) {

        console.error(error);

        showError(

            error.message ||

            "Unable to compare models."

        );

    }

}


/**********************************************************************
 * Main Renderer
 *********************************************************************/

function renderComparison() {

    if (!comparisonData) return;

    renderRecommendationHero();

    renderLeaderboard();

    renderAIScores();

    renderMetricWinners();

    renderPredictionCards();

    renderMetricsTable();

    renderStrengthWeakness();

    renderMetadata();

    renderScoreBreakdown();

    renderRadarChart();

    renderMetricsChart();

    animateProgressBars();

}



/**********************************************************************
 * Page States
 *********************************************************************/

function showLoading() {

    hideAllStates();

    document
        .getElementById("compLoading")
        ?.classList.remove("hidden");

}


function showContent() {

    hideAllStates();

    document
        .getElementById("compContent")
        ?.classList.remove("hidden");

}


function showEmpty() {

    hideAllStates();

    document
        .getElementById("compEmpty")
        ?.classList.remove("hidden");

}


function showError(message) {

    hideAllStates();

    document
        .getElementById("compError")
        ?.classList.remove("hidden");

    document
        .getElementById("compErrorMessage")
        .textContent = message;

}


function hideAllStates() {

    [

        "compLoading",

        "compContent",

        "compError",

        "compEmpty"

    ]

    .forEach(id =>

        document
            .getElementById(id)
            ?.classList.add("hidden")

    );

}

/**********************************************************************
 * Recommendation Hero
 *********************************************************************/

function renderRecommendationHero() {

    const container = document.getElementById("recommendedBanner");

    if (!container) return;

    const winner = comparisonData.recommended_model;

    const winnerData = comparisonData.comparison[winner];

    container.innerHTML = `

        <div class="hero-banner">

            <div class="hero-left">

                <div class="hero-badge">

                    🏆 AI Recommendation

                </div>

                <h1 class="hero-model">

                    ${winner}

                </h1>

                <p class="hero-reason">

                    ${comparisonData.recommendation_reason}

                </p>

            </div>

            <div class="hero-right">

                <div class="hero-score">

                    <span class="score-number">

                        ${winnerData.ai_score.toFixed(1)}

                    </span>

                    <span class="score-label">

                        AI Score

                    </span>

                </div>

                <div class="hero-confidence">

                    Confidence

                    <strong>

                        ${winnerData.confidence_score.toFixed(1)}%

                    </strong>

                </div>

            </div>

        </div>

    `;

}


/**********************************************************************
 * Leaderboard
 *********************************************************************/

function renderLeaderboard() {

    const container = document.getElementById("leaderboardBody");

    if (!container) return;

    container.innerHTML = "";

    comparisonData.leaderboard.forEach((model, index) => {

        const medal =
            index === 0 ? "🥇" :
            index === 1 ? "🥈" :
            "🥉";

        container.innerHTML += `

        <div class="leader-card">

            <div class="leader-rank">

                ${medal}

            </div>

            <div class="leader-info">

                <div class="leader-name">

                    ${model.model}

                </div>

                <div class="leader-stats">

                    Confidence

                    ${model.confidence.toFixed(1)}%

                </div>

            </div>

            <div class="leader-score">

                ${model.ai_score.toFixed(1)}

            </div>

        </div>

        `;

    });

}


/**********************************************************************
 * AI Scores
 *********************************************************************/

function renderAIScores() {

    const container = document.getElementById("scoresBody");

    if (!container) return;

    container.innerHTML = "";

    comparisonData.leaderboard.forEach(model => {

        container.innerHTML += `

        <div class="score-card">

            <div class="score-header">

                <span>

                    ${model.model}

                </span>

                <strong>

                    ${model.ai_score.toFixed(1)}

                </strong>

            </div>

            <div class="progress">

                <div

                    class="progress-fill"

                    style="width:0%"
                    data-width="${model.ai_score}">

                </div>

            </div>

        </div>

        `;

    });

}
function animateProgressBars(){

document
.querySelectorAll(".progress-fill")
.forEach(bar=>{

const w=bar.dataset.width;

setTimeout(()=>{

bar.style.width=w+"%";

},200);

});

}

/**********************************************************************
 * Metric Winners
 *********************************************************************/

function renderMetricWinners() {

    const container = document.getElementById("metricWinnersBody");

    if (!container) return;

    container.innerHTML = "";

    const winners = comparisonData.metric_winners;

    const icons = {
        prediction_accuracy: "🎯",
        rmse: "📉",
        mae: "📊",
        mape: "📈",
        direction_accuracy: "🧭",
        r2_score: "📐",
        confidence: "⭐"
    };

    Object.entries(winners).forEach(([metric, winner]) => {

        const title = metric
            .replaceAll("_", " ")
            .replace(/\b\w/g, c => c.toUpperCase());

        container.innerHTML += `

        <div class="winner-card">

            <div class="winner-icon">

                ${icons[metric] || "🏅"}

            </div>

            <div class="winner-title">

                ${title}

            </div>

            <div class="winner-model">

                ${winner}

            </div>

        </div>

        `;

    });

}


/**********************************************************************
 * Prediction Comparison
 *********************************************************************/

function renderPredictionCards() {

    const container = document.getElementById("predictionCompareBody");

    if (!container) return;

    container.innerHTML = "";

    Object.entries(comparisonData.comparison).forEach(([model, data]) => {

        container.innerHTML += `

        <div class="prediction-card">

            <div class="prediction-header">

                ${model}

            </div>

            <div class="prediction-price">

                $${data.predicted_price.toFixed(2)}

            </div>

            <div class="prediction-row">

                <span>Actual</span>

                <strong>

                    $${data.actual_price.toFixed(2)}

                </strong>

            </div>

            <div class="prediction-row">

                <span>Confidence</span>

                <strong>

                    ${data.confidence_score.toFixed(1)}%

                </strong>

            </div>

            <div class="prediction-row">

                <span>AI Score</span>

                <strong>

                    ${data.ai_score.toFixed(1)}

                </strong>

            </div>

        </div>

        `;

    });

}


/**********************************************************************
 * Detailed Metrics Table
 *********************************************************************/

function renderMetricsTable() {

    const container = document.getElementById("metricsTableBody");

    if (!container) return;

    const models = Object.keys(comparisonData.comparison);

    const metricMap = [
        ["Prediction Accuracy", "prediction_accuracy_percent"],
        ["Direction Accuracy", "direction_accuracy"],
        ["RMSE", "rmse"],
        ["MAE", "mae"],
        ["MAPE", "mape"],
        ["R² Score", "r2_score"],
        ["Confidence", "confidence_score"],
        ["AI Score", "ai_score"]
    ];

    let html = `
        <table class="metrics-table">

            <thead>

                <tr>
                    <th>Metric</th>
                    <th>${models[0]}</th>
                    <th>${models[1]}</th>
                    <th>Winner</th>
                </tr>

            </thead>

            <tbody>
    `;

    metricMap.forEach(([title, key]) => {

        const a = comparisonData.comparison[models[0]];
        const b = comparisonData.comparison[models[1]];

        const valueA =
            key === "confidence_score"
                ? a.confidence_score
                : key === "ai_score"
                ? a.ai_score
                : a.metrics[key];

        const valueB =
            key === "confidence_score"
                ? b.confidence_score
                : key === "ai_score"
                ? b.ai_score
                : b.metrics[key];

        let winner;

        if (["rmse", "mae", "mape"].includes(key)) {

            winner = valueA < valueB
                ? models[0]
                : models[1];

        } else {

            winner = valueA > valueB
                ? models[0]
                : models[1];

        }

        const classA = winner === models[0]
            ? "best-cell"
            : "";

        const classB = winner === models[1]
            ? "best-cell"
            : "";

        html += `

            <tr>

                <td>${title}</td>

                <td class="${classA}">
                    ${Number(valueA).toFixed(2)}
                </td>

                <td class="${classB}">
                    ${Number(valueB).toFixed(2)}
                </td>

                <td>

                    <span class="winner-badge">

                        ${winner}

                    </span>

                </td>

            </tr>

        `;

    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;

}

/**********************************************************************
 * Strengths & Weaknesses
 *********************************************************************/

function renderStrengthWeakness() {

    const container = document.getElementById("strengthsWeaknessesBody");

    if (!container) return;

    container.innerHTML = "";

    Object.entries(comparisonData.comparison).forEach(([model, data]) => {

        const strengths = data.strengths || [];
        const weaknesses = data.weaknesses || [];

        container.innerHTML += `

        <div class="model-analysis-card">

            <h3>${model}</h3>

            <div class="analysis-section">

                <h4 class="strength-title">

                    <i class="fas fa-circle-check"></i>

                    Strengths

                </h4>

                <ul>

                    ${strengths.map(s => `
                        <li>${s}</li>
                    `).join("")}

                </ul>

            </div>

            <div class="analysis-section">

                <h4 class="weakness-title">

                    <i class="fas fa-triangle-exclamation"></i>

                    Weaknesses

                </h4>

                <ul>

                    ${weaknesses.map(w => `
                        <li>${w}</li>
                    `).join("")}

                </ul>

            </div>

        </div>

        `;

    });

}

/**********************************************************************
 * Model Metadata
 *********************************************************************/

function renderMetadata() {

    const container = document.getElementById("metadataBody");

    if (!container) return;

    container.innerHTML = "";

    Object.entries(comparisonData.metadata).forEach(([model, meta]) => {

        container.innerHTML += `

        <div class="metadata-card">

            <h3>${model}</h3>

            <div class="metadata-grid">

                <div>

                    <label>Training Date</label>

                    <strong>${meta.training_date || "N/A"}</strong>

                </div>

                <div>

                    <label>Training Rows</label>

                    <strong>${meta.training_rows || "N/A"}</strong>

                </div>

                <div>

                    <label>Features</label>

                    <strong>${meta.feature_count || "N/A"}</strong>

                </div>

                <div>

                    <label>Model Version</label>

                    <strong>${meta.version || "1.0"}</strong>

                </div>

            </div>

        </div>

        `;

    });

}

/**********************************************************************
 * AI Score Breakdown
 *********************************************************************/

function renderScoreBreakdown() {

    const container = document.getElementById("scoreBreakdownBody");

    if (!container) return;

    const weights = [

        ["Prediction Accuracy",30],

        ["RMSE",20],

        ["MAE",15],

        ["MAPE",10],

        ["Direction Accuracy",10],

        ["R² Score",10],

        ["Confidence",5]

    ];

    container.innerHTML = "";

    weights.forEach(([metric, weight]) => {

        container.innerHTML += `

        <div class="breakdown-item">

            <div class="breakdown-header">

                <span>${metric}</span>

                <strong>${weight}%</strong>

            </div>

            <div class="progress">

                <div

                    class="progress-fill"

                    style="width:${weight * 3}%">

                </div>

            </div>

        </div>

        `;

    });

}

/**********************************************************************
 * Radar Chart
 *********************************************************************/

function renderRadarChart() {

    const ctx = document.getElementById("radarChart");

    if (!ctx) return;

    if (radarChart) radarChart.destroy();

    const models = Object.keys(comparisonData.comparison);

    radarChart = new Chart(ctx, {

        type: "radar",

        data: {

            labels: [

                "Accuracy",

                "Direction",

                "Confidence",

                "AI Score"

            ],

            datasets: models.map((model, index) => {

                const d = comparisonData.comparison[model];

                return {

                    label: model,

                    data: [

                        d.metrics.prediction_accuracy_percent,

                        d.metrics.direction_accuracy,

                        d.confidence_score,

                        d.ai_score

                    ]

                };

            })

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    position: "bottom"

                }

            },

            scales: {

                r: {

                    min: 0,

                    max: 100

                }

            }

        }

    });

}

function renderMetricsChart() {

    const canvas = document.getElementById("barChart");

    if (!canvas) return;

    if (metricsChart) {
        metricsChart.destroy();
    }

    const models = Object.keys(comparisonData.comparison);

    metricsChart = new Chart(canvas, {

        type: "bar",

        data: {

            labels: ["RMSE", "MAE", "MAPE"],

            datasets: models.map(model => {

                const m = comparisonData.comparison[model];

                return {

                    label: model,

                    data: [

                        m.metrics.rmse,

                        m.metrics.mae,

                        m.metrics.mape

                    ]

                };

            })

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    position: "bottom"

                }

            }

        }

    });

}