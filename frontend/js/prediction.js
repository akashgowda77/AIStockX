/**
 * AIStockX - Prediction Module
 * Single responsibility: AI Prediction page (train, predict, retrain both models)
 * Uses: api.js for all fetch calls
 */

// =============================================================================
// State
// =============================================================================

let currentPredSymbol = '';
let linearState = { trained: false, metrics: null, prediction: null };
let lstmState = { trained: false, metrics: null, prediction: null };

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', function () {
    initAuthenticatedPage('prediction');
});

// =============================================================================
// Load Prediction Page
// =============================================================================

async function loadPredictionPage() {
    const input = document.getElementById('predSymbolInput');
    const symbol = input.value.trim().toUpperCase();

    if (!symbol) {
        showToast('Please enter a stock symbol', 'warning');
        return;
    }

    currentPredSymbol = symbol;

    // Reset states
    linearState = { trained: false, metrics: null, prediction: null };
    lstmState = { trained: false, metrics: null, prediction: null };

    // Show content, hide empty
    document.getElementById('predEmpty').classList.add('hidden');
    document.getElementById('predContent').classList.remove('hidden');

    // Reset UI
    resetModelCard('linear');
    resetModelCard('lstm');
    document.getElementById('predHistoryBody').innerHTML = `
        <p class="text-muted" style="text-align:center;padding:24px;">
            <i class="fas fa-chart-line" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
            Train a model to see performance metrics
        </p>
    `;

    showToast(`Loaded ${symbol}. Click Train to start.`, 'info');
}

// =============================================================================
// Reset Model Card UI
// =============================================================================

function resetModelCard(model) {
    const prefix = model;
    document.getElementById(`${prefix}StatusBadge`).textContent = 'Not Trained';
    document.getElementById(`${prefix}StatusBadge`).className = 'model-badge badge badge-info';
    document.getElementById(`${prefix}PredictBtn`).disabled = true;
    document.getElementById(`${prefix}Training`).classList.add('hidden');
    document.getElementById(`${prefix}Result`).classList.add('hidden');
    document.getElementById(`${prefix}Result`).innerHTML = '';
}

// =============================================================================
// Train Model
// =============================================================================

async function trainModel(model) {
    if (!currentPredSymbol) {
        showToast('Please enter a stock symbol first', 'warning');
        return;
    }

    const prefix = model;
    const btn = document.getElementById(`${prefix}TrainBtn`);
    const trainingDiv = document.getElementById(`${prefix}Training`);
    const resultDiv = document.getElementById(`${prefix}Result`);

    // Show training state
    btn.disabled = true;
    trainingDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');

    try {
        let trainResponse;
        if (model === 'linear') {
            trainResponse = await predictionsApi.trainLinear(currentPredSymbol);
        } else {
            trainResponse = await predictionsApi.trainLSTM(currentPredSymbol);
        }

        // Hide training
        trainingDiv.classList.add('hidden');
        btn.disabled = false;

        if (trainResponse.success && trainResponse.data) {
            const data = trainResponse.data;

            // Update state
            if (model === 'linear') {
                linearState.trained = true;
                linearState.metrics = data.metrics || {};
                linearState.prediction = data.prediction || null;
            } else {
                lstmState.trained = true;
                lstmState.metrics = data.metrics || {};
                lstmState.prediction = data.prediction || null;
            }

            // Update badge
            const statusBadge = document.getElementById(`${prefix}StatusBadge`);
            statusBadge.textContent = 'Trained';
            statusBadge.className = 'model-badge badge badge-success';

            // Enable predict button
            document.getElementById(`${prefix}PredictBtn`).disabled = false;

            // Display result
            displayPredictionResult(model, data);

            // Update history
            updatePredictionHistory();

            showToast(`${model === 'linear' ? 'Linear Regression' : 'LSTM'} model trained successfully!`, 'success');
        }
    } catch (error) {
        trainingDiv.classList.add('hidden');
        btn.disabled = false;

        showToast(`Training failed: ${getErrorMessage(error)}`, 'error');
    }
}

// =============================================================================
// Predict Model
// =============================================================================

async function predictModel(model) {
    if (!currentPredSymbol) {
        showToast('Please enter a stock symbol first', 'warning');
        return;
    }

    const prefix = model;
    const resultDiv = document.getElementById(`${prefix}Result`);

    // Show loading in result area
    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = `
        <div class="training-spinner" style="margin-top:0;">
            <div class="spinner-ring" style="width:24px;height:24px;border-width:3px;"></div>
            <span>Generating prediction...</span>
        </div>
    `;

    try {
        let response;
        if (model === 'linear') {
            response = await predictionsApi.predictLinear(currentPredSymbol);
        } else {
            response = await predictionsApi.predictLSTM(currentPredSymbol);
        }

        if (response.success && response.data) {
            const data = response.data;

            // Update state
            if (model === 'linear') {
                linearState.prediction = data.prediction || null;
                linearState.metrics = data.metrics || {};
            } else {
                lstmState.prediction = data.prediction || null;
                lstmState.metrics = data.metrics || {};
            }

            displayPredictionResult(model, data);
            updatePredictionHistory();

            showToast('Prediction generated successfully!', 'success');
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div style="padding:16px;text-align:center;color:var(--color-danger);background:var(--color-danger-bg);border-radius:var(--radius-md);">
                <i class="fas fa-exclamation-circle"></i> ${getErrorMessage(error)}
            </div>
        `;
    }
}

// =============================================================================
// Retrain Model
// =============================================================================

async function retrainModel(model) {
    if (!currentPredSymbol) {
        showToast('Please enter a stock symbol first', 'warning');
        return;
    }

    const prefix = model;
    const btn = document.getElementById(`${prefix}RetrainBtn`);
    const trainingDiv = document.getElementById(`${prefix}Training`);
    const resultDiv = document.getElementById(`${prefix}Result`);

    // Show training state
    btn.disabled = true;
    trainingDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');

    try {
        let response;
        if (model === 'linear') {
            response = await predictionsApi.trainLinear(currentPredSymbol, true);
        } else {
            response = await predictionsApi.trainLSTM(currentPredSymbol, true);
        }

        trainingDiv.classList.add('hidden');
        btn.disabled = false;

        if (response.success && response.data) {
            const data = response.data;

            if (model === 'linear') {
                linearState.trained = true;
                linearState.metrics = data.metrics || {};
                linearState.prediction = data.prediction || null;
            } else {
                lstmState.trained = true;
                lstmState.metrics = data.metrics || {};
                lstmState.prediction = data.prediction || null;
            }

            const statusBadge = document.getElementById(`${prefix}StatusBadge`);
            statusBadge.textContent = 'Trained';
            statusBadge.className = 'model-badge badge badge-success';

            document.getElementById(`${prefix}PredictBtn`).disabled = false;

            displayPredictionResult(model, data);
            updatePredictionHistory();

            showToast(`${model === 'linear' ? 'Linear Regression' : 'LSTM'} model retrained!`, 'success');
        }
    } catch (error) {
        trainingDiv.classList.add('hidden');
        btn.disabled = false;
        showToast(`Retrain failed: ${getErrorMessage(error)}`, 'error');
    }
}

// =============================================================================
// Display Prediction Result
// =============================================================================

function displayPredictionResult(model, data) {
    const prefix = model;
    const resultDiv = document.getElementById(`${prefix}Result`);
    resultDiv.classList.remove('hidden');

    const prediction = data.prediction || {};
    const metrics = data.metrics || {};

    const predictedPrice = prediction.predicted_price;
    const actualPrice = prediction.actual_price;
    const error = prediction.error;
    const confidence = prediction.confidence_score;

    // Price grid
    let priceHtml = `
        <div class="prediction-price-grid">
            <div class="pred-price-item">
                <div class="price-label">Predicted Price</div>
                <div class="price-value" style="color:var(--color-primary);">
                    ${predictedPrice ? formatCurrency(predictedPrice) : '—'}
                </div>
            </div>
            <div class="pred-price-item">
                <div class="price-label">Actual Price</div>
                <div class="price-value">
                    ${actualPrice ? formatCurrency(actualPrice) : 'N/A'}
                </div>
            </div>
            <div class="pred-price-item">
                <div class="price-label">Error</div>
                <div class="price-value ${error >= 0 ? 'text-success' : 'text-danger'}">
                    ${error !== null && error !== undefined ? formatCurrency(error) : '—'}
                </div>
            </div>
        </div>
    `;

    // Confidence bar
    const confidenceColor = confidence >= 70 ? 'var(--color-success)' : confidence >= 50 ? 'var(--color-warning)' : 'var(--color-danger)';
    let confidenceHtml = `
        <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:var(--color-bg);border-radius:var(--radius-md);margin-bottom:16px;">
            <span style="font-size:0.85rem;font-weight:600;">Confidence</span>
            <div class="confidence-bar" style="flex:1;">
                <div class="confidence-fill" style="width:${confidence || 0}%;background:${confidenceColor};"></div>
            </div>
            <span class="confidence-text" style="color:${confidenceColor};">${confidence ? confidence.toFixed(1) + '%' : '—'}</span>
        </div>
    `;

    // Metrics grid
    const metricKeys = [
        { key: 'rmse', label: 'RMSE', fn: v => formatNumber(v) },
        { key: 'mae', label: 'MAE', fn: v => formatNumber(v) },
        { key: 'mape', label: 'MAPE', fn: v => formatNumber(v) + '%' },
        { key: 'r2', label: 'R²', fn: v => formatNumber(v) },
        { key: 'direction_accuracy', label: 'Direction Accuracy', fn: v => formatPercent(v) },
        { key: 'prediction_accuracy_percent', label: 'Prediction Accuracy', fn: v => formatNumber(v) + '%' },
    ];

    let metricsHtml = '<div class="pred-metrics-grid">';
    metricKeys.forEach(m => {
        const value = metrics[m.key];
        metricsHtml += `
            <div class="pred-metric-item">
                <div class="metric-label">${m.label}</div>
                <div class="metric-value">${value !== null && value !== undefined ? m.fn(value) : '—'}</div>
            </div>
        `;
    });
    metricsHtml += '</div>';

    resultDiv.innerHTML = priceHtml + confidenceHtml + metricsHtml;
}

// =============================================================================
// Update Prediction History Section
// =============================================================================

function updatePredictionHistory() {
    const historyBody = document.getElementById('predHistoryBody');

    const linearMetrics = linearState.metrics;
    const lstmMetrics = lstmState.metrics;

    const hasLinear = linearState.trained && linearMetrics && Object.keys(linearMetrics).length > 0;
    const hasLSTM = lstmState.trained && lstmMetrics && Object.keys(lstmMetrics).length > 0;

    if (!hasLinear && !hasLSTM) {
        historyBody.innerHTML = `
            <p class="text-muted" style="text-align:center;padding:24px;">
                <i class="fas fa-chart-line" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                Train a model to see performance metrics
            </p>
        `;
        return;
    }

    const metricKeys = [
        { key: 'rmse', label: 'RMSE' },
        { key: 'mae', label: 'MAE' },
        { key: 'mape', label: 'MAPE (%)' },
        { key: 'r2', label: 'R²' },
        { key: 'direction_accuracy', label: 'Direction Acc. (%)' },
        { key: 'prediction_accuracy_percent', label: 'Prediction Acc. (%)' },
    ];

    let tableHtml = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${hasLinear ? '<th>Linear Regression</th>' : ''}
                        ${hasLSTM ? '<th>LSTM</th>' : ''}
                    </tr>
                </thead>
                <tbody>
    `;

    metricKeys.forEach(m => {
        const linearVal = hasLinear ? linearMetrics[m.key] : null;
        const lstmVal = hasLSTM ? lstmMetrics[m.key] : null;

        tableHtml += `
            <tr>
                <td style="font-weight:600;">${m.label}</td>
                ${hasLinear ? `<td>${linearVal !== null && linearVal !== undefined ? formatNumber(linearVal) : '—'}</td>` : ''}
                ${hasLSTM ? `<td>${lstmVal !== null && lstmVal !== undefined ? formatNumber(lstmVal) : '—'}</td>` : ''}
            </tr>
        `;
    });

    // Add prediction prices row
    tableHtml += `
        <tr>
            <td style="font-weight:600;">Predicted Price</td>
            ${hasLinear ? `<td style="font-weight:700;color:var(--color-primary);">${linearState.prediction?.predicted_price ? formatCurrency(linearState.prediction.predicted_price) : '—'}</td>` : ''}
            ${hasLSTM ? `<td style="font-weight:700;color:#7c3aed;">${lstmState.prediction?.predicted_price ? formatCurrency(lstmState.prediction.predicted_price) : '—'}</td>` : ''}
        </tr>
        <tr>
            <td style="font-weight:600;">Confidence Score</td>
            ${hasLinear ? `<td>${linearState.prediction?.confidence_score ? formatNumber(linearState.prediction.confidence_score) + '%' : '—'}</td>` : ''}
            ${hasLSTM ? `<td>${lstmState.prediction?.confidence_score ? formatNumber(lstmState.prediction.confidence_score) + '%' : '—'}</td>` : ''}
        </tr>
    `;

    tableHtml += `
                </tbody>
            </table>
        </div>
    `;

    historyBody.innerHTML = tableHtml;
}