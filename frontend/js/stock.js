/**
 * AIStockX - Stock Module
 * Single responsibility: Stock detail page (company, quote, charts, indicators)
 * Uses: api.js for all fetch calls, charts.js for all Chart.js rendering
 */

// =============================================================================
// State
// =============================================================================

let currentSymbol = '';
let currentPeriod = '1y';
let historyData = [];
let indicatorData = null;

let priceChartInstance = null;
let volumeChartInstance = null;
let rsiChartInstance = null;
let macdChartInstance = null;
let stochChartInstance = null;

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', function () {
    initAuthenticatedPage('stock');
    initStockPage();
});

function initStockPage() {
    // Check for symbol in URL params
    const params = new URLSearchParams(window.location.search);
    const symbol = params.get('symbol');

    if (symbol) {
        document.getElementById('stockSymbolInput').value = symbol.toUpperCase();
        loadStock();
    }
}

// =============================================================================
// Load Stock
// =============================================================================

async function loadStock() {
    const input = document.getElementById('stockSymbolInput');
    const symbol = input.value.trim().toUpperCase();

    if (!symbol) {
        showToast('Please enter a stock symbol', 'warning');
        return;
    }

    currentSymbol = symbol;
    currentPeriod = '1y';

    // Hide previous results, show loading
    hideAllSections();
    document.getElementById('stockLoading').classList.remove('hidden');
    document.getElementById('stockError').classList.add('hidden');

    try {
        // Fetch all data in parallel
        const [companyRes, quoteRes, historyRes, indicatorsRes] = await Promise.all([
            stocksApi.getCompany(symbol),
            stocksApi.getQuote(symbol),
            stocksApi.getHistory(symbol, currentPeriod, '1d'),
            indicatorsApi.getIndicators(symbol),
        ]);

        historyData = historyRes.success ? historyRes.data.history : [];
        indicatorData = indicatorsRes;

        // Hide loading
        document.getElementById('stockLoading').classList.add('hidden');

        // Render everything
        renderStockHeader(companyRes, quoteRes);
        renderCompanyInfo(companyRes);
        renderQuoteInfo(quoteRes);
        renderPriceChart();
        renderVolumeChart();
        renderTrendSignal();
        renderIndicatorValues();
        renderIndicatorCharts();

        // Show sections with animation
        document.getElementById('stockHeader').classList.remove('hidden');
        document.getElementById('stockOverview').classList.remove('hidden');
        document.getElementById('priceChartSection').classList.remove('hidden');
        document.getElementById('volumeChartSection').classList.remove('hidden');
        document.getElementById('indicatorsSection').classList.remove('hidden');

    } catch (error) {
        document.getElementById('stockLoading').classList.add('hidden');
        document.getElementById('stockError').classList.remove('hidden');
        document.getElementById('errorMessage').textContent = getErrorMessage(error);
    }
}

function hideAllSections() {
    ['stockHeader', 'stockOverview', 'priceChartSection', 'volumeChartSection', 'indicatorsSection'].forEach(id => {
        document.getElementById(id).classList.add('hidden');
    });
}

// =============================================================================
// Stock Header
// =============================================================================

function renderStockHeader(companyRes, quoteRes) {
    const header = document.getElementById('stockHeader');
    const symbol = currentSymbol;
    const company = companyRes.success ? companyRes.data : null;
    const quote = quoteRes.success ? quoteRes.data : null;

    const name = company?.name || symbol;
    const exchange = company?.exchange || '';
    const price = quote?.price || null;
    const change = quote?.change || null;
    const percentChange = quote?.percent_change || null;

    const changeClass = change >= 0 ? 'text-success' : 'text-danger';
    const changeIcon = change >= 0 ? 'fa-caret-up' : 'fa-caret-down';

    header.innerHTML = `
        <div class="stock-header-left">
            <div class="stock-avatar">${symbol.charAt(0)}</div>
            <div class="stock-title">
                <h1>${symbol}</h1>
                <p>${name} ${exchange ? '• ' + exchange : ''}</p>
            </div>
        </div>
        <div class="stock-header-right">
            <div class="stock-price">${price ? formatCurrency(price) : '—'}</div>
            <div class="stock-change ${changeClass}">
                ${change !== null ? `<i class="fas ${changeIcon}"></i> ${formatCurrency(change)}` : '—'}
                ${percentChange !== null ? `(${formatPercent(percentChange)})` : ''}
            </div>
        </div>
    `;
}

// =============================================================================
// Company Info
// =============================================================================

function renderCompanyInfo(companyRes) {
    const companyDiv = document.getElementById('companyInfo');

    if (!companyRes.success || !companyRes.data) {
        companyDiv.innerHTML = `<p class="text-muted">Company information unavailable</p>`;
        return;
    }

    const c = companyRes.data;
    companyDiv.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Sector</p>
                <p style="font-weight:500;margin-top:2px;">${c.sector || 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Industry</p>
                <p style="font-weight:500;margin-top:2px;">${c.industry || 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Market Cap</p>
                <p style="font-weight:500;margin-top:2px;">${c.market_cap ? formatCompactNumber(c.market_cap) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">P/E Ratio</p>
                <p style="font-weight:500;margin-top:2px;">${c.pe_ratio ? formatNumber(c.pe_ratio) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">EPS</p>
                <p style="font-weight:500;margin-top:2px;">${c.eps ? formatCurrency(c.eps) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Dividend Yield</p>
                <p style="font-weight:500;margin-top:2px;">${c.dividend_yield ? (c.dividend_yield * 100).toFixed(2) + '%' : 'N/A'}</p>
            </div>
            <div style="grid-column:1/-1;">
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">52-Week Range</p>
                <p style="font-weight:500;margin-top:2px;">
                    ${c['52_week_low'] ? formatCurrency(c['52_week_low']) : 'N/A'}
                    —
                    ${c['52_week_high'] ? formatCurrency(c['52_week_high']) : 'N/A'}
                </p>
            </div>
            ${c.website ? `
            <div style="grid-column:1/-1;">
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Website</p>
                <p style="font-weight:500;margin-top:2px;">
                    <a href="${c.website}" target="_blank" style="color:var(--color-primary);">${c.website}</a>
                </p>
            </div>` : ''}
        </div>
        ${c.description ? `
        <div class="divider"></div>
        <div>
            <p style="font-size:0.85rem;color:var(--color-text-secondary);line-height:1.6;">
                ${c.description.length > 300 ? c.description.substring(0, 300) + '...' : c.description}
            </p>
        </div>` : ''}
    `;
}

// =============================================================================
// Quote Info
// =============================================================================

function renderQuoteInfo(quoteRes) {
    const quoteDiv = document.getElementById('quoteInfo');

    if (!quoteRes.success || !quoteRes.data) {
        quoteDiv.innerHTML = `<p class="text-muted">Quote data unavailable</p>`;
        return;
    }

    const q = quoteRes.data;
    const changeClass = q.change >= 0 ? 'text-success' : 'text-danger';
    const changeIcon = q.change >= 0 ? 'fa-caret-up' : 'fa-caret-down';

    quoteDiv.innerHTML = `
        <div style="text-align:center;padding:8px 0;">
            <p style="font-size:2.5rem;font-weight:700;letter-spacing:-1px;">
                ${formatCurrency(q.price)}
            </p>
            <p class="${changeClass}" style="font-size:1.1rem;font-weight:600;margin-top:4px;">
                <i class="fas ${changeIcon}"></i>
                ${q.change !== null ? formatCurrency(q.change) : 'N/A'}
                (${q.percent_change !== null ? formatPercent(q.percent_change) : 'N/A'})
            </p>
        </div>
        <div class="divider"></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Open</p>
                <p style="font-weight:500;margin-top:2px;">${q.open ? formatCurrency(q.open) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Previous Close</p>
                <p style="font-weight:500;margin-top:2px;">${q.previous_close ? formatCurrency(q.previous_close) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Day High</p>
                <p style="font-weight:500;margin-top:2px;">${q.day_high ? formatCurrency(q.day_high) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Day Low</p>
                <p style="font-weight:500;margin-top:2px;">${q.day_low ? formatCurrency(q.day_low) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Volume</p>
                <p style="font-weight:500;margin-top:2px;">${q.volume ? formatCompactNumber(q.volume) : 'N/A'}</p>
            </div>
            <div>
                <p style="font-size:0.75rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;">Market State</p>
                <p style="font-weight:500;margin-top:2px;">${q.market_state || 'N/A'}</p>
            </div>
        </div>
    `;
}

// =============================================================================
// Price Chart
// =============================================================================

function renderPriceChart() {
    destroyChart(priceChartInstance);

    if (!historyData || historyData.length === 0) return;

    const labels = historyData.map(row => row.date);
    const prices = historyData.map(row => row.close);

    // Determine chart color based on trend
    const firstPrice = prices[0];
    const lastPrice = prices[prices.length - 1];
    const chartColor = lastPrice >= firstPrice ? '#0ecb81' : '#f6465d';

    priceChartInstance = createPriceChart('priceChart', labels, prices, chartColor);
}

// =============================================================================
// Volume Chart
// =============================================================================

function renderVolumeChart() {
    destroyChart(volumeChartInstance);

    if (!historyData || historyData.length === 0) return;

    const labels = historyData.map(row => row.date);
    const volumes = historyData.map(row => row.volume || 0);

    volumeChartInstance = createVolumeChart('volumeChart', labels, volumes);
}

// =============================================================================
// Change Period
// =============================================================================

async function changePeriod(period) {
    if (!currentSymbol) return;

    currentPeriod = period;

    // Update active button
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.period === period);
    });

    try {
        const historyRes = await stocksApi.getHistory(currentSymbol, period, '1d');
        if (historyRes.success && historyRes.data) {
            historyData = historyRes.data.history || [];
            renderPriceChart();
            renderVolumeChart();
        }
    } catch (error) {
        showToast('Failed to load data for this period', 'error');
    }
}

// =============================================================================
// Trend Signal
// =============================================================================

function renderTrendSignal() {
    const container = document.getElementById('trendSignal');

    if (!indicatorData || !indicatorData.success || !indicatorData.data) {
        container.innerHTML = `<p class="text-muted">Trend signal unavailable</p>`;
        return;
    }

    const trend = indicatorData.data.trend;
    if (!trend) {
        container.innerHTML = `<p class="text-muted">Trend signal unavailable</p>`;
        return;
    }

    const signal = trend.overall_signal || 'Neutral';
    const confidence = trend.confidence || 0;
    const signals = trend.signals || {};

    const signalLower = signal.toLowerCase();
    const signalClass = signalLower === 'bullish' ? 'signal-bullish' : signalLower === 'bearish' ? 'signal-bearish' : 'signal-neutral';
    const signalIcon = signalLower === 'bullish' ? 'fa-arrow-trend-up' : signalLower === 'bearish' ? 'fa-arrow-trend-down' : 'fa-minus';
    const confidenceColor = confidence >= 60 ? 'var(--color-success)' : confidence >= 40 ? 'var(--color-warning)' : 'var(--color-danger)';

    let detailsHtml = '';
    Object.entries(signals).forEach(([indicator, value]) => {
        const valLower = value.toLowerCase();
        detailsHtml += `
            <div class="trend-signal-detail-item">
                <span class="detail-dot ${valLower}"></span>
                <span>${indicator}: <strong class="text-${valLower === 'bullish' ? 'success' : valLower === 'bearish' ? 'danger' : 'muted'}">${value}</strong></span>
            </div>
        `;
    });

    container.innerHTML = `
        <div class="trend-signal-badge ${signalClass}">
            <i class="fas ${signalIcon} signal-icon"></i>
            <span class="signal-label">Overall Signal</span>
            <span class="signal-text">${signal}</span>
            <div class="confidence-bar-container">
                <span style="font-size:0.85rem;">Confidence</span>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width:${confidence}%;background:${confidenceColor};"></div>
                </div>
                <span class="confidence-text" style="color:${confidenceColor};">${confidence.toFixed(0)}%</span>
            </div>
        </div>
        <div class="trend-signal-details">
            ${detailsHtml}
        </div>
    `;
}

// =============================================================================
// Indicator Values
// =============================================================================

function renderIndicatorValues() {
    const container = document.getElementById('indicatorValues');

    if (!indicatorData || !indicatorData.success || !indicatorData.data) {
        container.innerHTML = `<p class="text-muted">Indicator values unavailable</p>`;
        return;
    }

    const latest = indicatorData.data.latest;
    if (!latest) {
        container.innerHTML = `<p class="text-muted">Indicator values unavailable</p>`;
        return;
    }

    const indicators = [
        { name: 'Close Price', key: 'close', fn: v => formatCurrency(v) },
        { name: 'SMA (20)', key: 'sma_20', fn: v => formatCurrency(v) },
        { name: 'EMA (20)', key: 'ema_20', fn: v => formatCurrency(v) },
        { name: 'RSI (14)', key: 'rsi_14', fn: v => formatNumber(v), colorize: true },
        { name: 'MACD', key: 'macd', fn: v => formatNumber(v), colorize: true },
        { name: 'MACD Signal', key: 'macd_signal', fn: v => formatNumber(v) },
        { name: 'MACD Histogram', key: 'macd_hist', fn: v => formatNumber(v), colorize: true },
        { name: 'BB Upper', key: 'bb_upper', fn: v => formatCurrency(v) },
        { name: 'BB Middle', key: 'bb_middle', fn: v => formatCurrency(v) },
        { name: 'BB Lower', key: 'bb_lower', fn: v => formatCurrency(v) },
        { name: 'ATR (14)', key: 'atr_14', fn: v => formatCurrency(v) },
        { name: 'OBV', key: 'obv', fn: v => formatCompactNumber(v) },
        { name: 'Stoch %K (14)', key: 'stoch_k_14', fn: v => formatNumber(v), colorize: true },
        { name: 'Stoch %D (14)', key: 'stoch_d_14', fn: v => formatNumber(v), colorize: true },
    ];

    let html = '';
    indicators.forEach(ind => {
        const value = latest[ind.key];
        if (value === null || value === undefined) return;

        let valueClass = '';
        if (ind.colorize) {
            if (ind.key === 'rsi_14') {
                valueClass = value >= 70 ? 'value-bearish' : value <= 30 ? 'value-bullish' : 'value-neutral';
            } else if (ind.key === 'macd_hist') {
                valueClass = value >= 0 ? 'value-bullish' : 'value-bearish';
            } else if (ind.key === 'macd') {
                valueClass = value >= 0 ? 'value-bullish' : 'value-bearish';
            } else if (ind.key.startsWith('stoch')) {
                valueClass = value >= 80 ? 'value-bearish' : value <= 20 ? 'value-bullish' : 'value-neutral';
            }
        }

        html += `
            <div class="indicator-item">
                <div class="indicator-name">${ind.name}</div>
                <div class="indicator-value ${valueClass}">${ind.fn(value)}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// =============================================================================
// Indicator Charts
// =============================================================================

function renderIndicatorCharts() {
    if (!indicatorData || !indicatorData.success || !indicatorData.data) return;

    const latest = indicatorData.data.latest;
    if (!latest) return;

    // For indicator charts we need historical indicator data.
    // The backend currently returns only latest values, so we compute
    // basic series from the price history for visualization.
    if (!historyData || historyData.length < 30) return;

    const labels = historyData.map(row => row.date);
    const closes = historyData.map(row => row.close);
    const highs = historyData.map(row => row.high);
    const lows = historyData.map(row => row.low);

    // RSI Chart
    destroyChart(rsiChartInstance);
    const rsiValues = computeRSI(closes, 14);
    if (rsiValues) {
        const rsiLabels = labels.slice(-rsiValues.length);
        // Add overbought/oversold lines via mixed dataset approach
        rsiChartInstance = createIndicatorChart('rsiChart', rsiLabels, rsiValues, 'RSI (14)', '#7c3aed', 'line');
    }

    // MACD Chart
    destroyChart(macdChartInstance);
    const macdResult = computeMACD(closes);
    if (macdResult) {
        const macdLabels = labels.slice(-macdResult.macd.length);
        // Use the histogram with bar type
        macdChartInstance = createIndicatorChart('macdChart', macdLabels, macdResult.histogram, 'MACD Histogram', '#0891b2', 'bar');
    }

    // Stochastic Chart
    destroyChart(stochChartInstance);
    const stochResult = computeStochastic(highs, lows, closes, 14);
    if (stochResult) {
        const stochLabels = labels.slice(-stochResult.k.length);
        stochChartInstance = createIndicatorChart('stochChart', stochLabels, stochResult.k, 'Stoch %K', '#f59e0b', 'line');
    }
}

// =============================================================================
// Client-side Technical Indicator Calculations (for charting)
// =============================================================================

function computeRSI(prices, period) {
    if (!prices || prices.length < period + 1) return null;

    const changes = [];
    for (let i = 1; i < prices.length; i++) {
        changes.push(prices[i] - prices[i - 1]);
    }

    const rsiValues = [];
    let avgGain = 0;
    let avgLoss = 0;

    // First average
    for (let i = 0; i < period; i++) {
        if (changes[i] >= 0) avgGain += changes[i];
        else avgLoss += Math.abs(changes[i]);
    }
    avgGain /= period;
    avgLoss /= period;

    rsiValues.push(100 - (100 / (1 + (avgGain / (avgLoss || 0.001)))));

    // Subsequent values
    for (let i = period; i < changes.length; i++) {
        const gain = changes[i] >= 0 ? changes[i] : 0;
        const loss = changes[i] < 0 ? Math.abs(changes[i]) : 0;

        avgGain = ((avgGain * (period - 1)) + gain) / period;
        avgLoss = ((avgLoss * (period - 1)) + loss) / period;

        rsiValues.push(100 - (100 / (1 + (avgGain / (avgLoss || 0.001)))));
    }

    return rsiValues;
}

function computeMACD(prices) {
    if (!prices || prices.length < 35) return null;

    const ema12 = computeEMA(prices, 12);
    const ema26 = computeEMA(prices, 26);

    const macdLine = [];
    for (let i = 0; i < ema26.length; i++) {
        const idx = ema12.length - ema26.length + i;
        macdLine.push(ema12[idx] - ema26[i]);
    }

    const signal = computeEMA(macdLine, 9);
    const histogram = [];
    for (let i = 0; i < signal.length; i++) {
        histogram.push(macdLine[macdLine.length - signal.length + i] - signal[i]);
    }

    return { macd: macdLine, signal, histogram };
}

function computeEMA(prices, period) {
    const k = 2 / (period + 1);
    const ema = [prices[0]];

    for (let i = 1; i < prices.length; i++) {
        ema.push((prices[i] - ema[i - 1]) * k + ema[i - 1]);
    }

    return ema;
}

function computeStochastic(highs, lows, closes, period) {
    if (!highs || highs.length < period) return null;

    const kValues = [];
    for (let i = period - 1; i < highs.length; i++) {
        const highMax = Math.max(...highs.slice(i - period + 1, i + 1));
        const lowMin = Math.min(...lows.slice(i - period + 1, i + 1));
        const close = closes[i];

        const k = ((close - lowMin) / (highMax - lowMin || 1)) * 100;
        kValues.push(k);
    }

    // Smooth %K into %D (3-period SMA)
    const dValues = [];
    for (let i = 2; i < kValues.length; i++) {
        dValues.push((kValues[i] + kValues[i - 1] + kValues[i - 2]) / 3);
    }

    return { k: kValues, d: dValues };
}