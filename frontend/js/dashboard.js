/**
 * AIStockX - Dashboard Module
 * Single responsibility: Dashboard page functionality
 * Uses: api.js for all fetch calls
 */

// =============================================================================
// Dashboard Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', function () {
    initAuthenticatedPage('dashboard');
    initDashboard();
});

function initDashboard() {
    const user = getUser();
    if (user) {
        document.getElementById('welcomeMessage').textContent =
            `Welcome back, ${user.username}!`;
    }
}

// =============================================================================
// Stock Search
// =============================================================================

let searchTimeout = null;

async function searchStock() {
    const input = document.getElementById('stockSearchInput');
    const symbol = input.value.trim().toUpperCase();

    if (!symbol) {
        showToast('Please enter a stock symbol', 'warning');
        return;
    }

    showLoading();
    const resultsDiv = document.getElementById('searchResults');
    const stockInfoDiv = document.getElementById('stockInfo');

    try {
        // Search for the stock
        const searchResponse = await stocksApi.search(symbol);

        if (searchResponse.success && searchResponse.data) {
            const stockData = searchResponse.data;

            // Display search result
            resultsDiv.classList.remove('hidden');
            resultsDiv.innerHTML = `
                <div class="card fade-in">
                    <div class="card-body" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
                        <div>
                            <h3 style="font-size:1.3rem;font-weight:700;">${stockData.symbol}</h3>
                            <p style="color:var(--color-text-secondary);margin-top:4px;">${stockData.name || 'N/A'}</p>
                            <p style="font-size:0.85rem;color:var(--color-text-muted);margin-top:2px;">
                                ${stockData.exchange || ''} ${stockData.exchange && stockData.currency ? '•' : ''} ${stockData.currency || ''}
                            </p>
                        </div>
                        <div style="display:flex;gap:8px;">
                            <button class="btn btn-primary" onclick="navigateToStock('${stockData.symbol}')">
                                <i class="fas fa-chart-line"></i> Analyze
                            </button>
                        </div>
                    </div>
                </div>
            `;

            // Store selected stock
            setSelectedStock(stockData);

            // Fetch company info and quote in parallel
            await Promise.all([
                fetchCompanyInfo(stockData.symbol),
                fetchQuote(stockData.symbol),
            ]);

            stockInfoDiv.classList.remove('hidden');
        } else {
            resultsDiv.classList.remove('hidden');
            resultsDiv.innerHTML = `
                <div class="card fade-in">
                    <div class="card-body">
                        <p style="color:var(--color-text-muted);text-align:center;padding:20px;">
                            <i class="fas fa-search" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                            No results found for "${symbol}"
                        </p>
                    </div>
                </div>
            `;
            stockInfoDiv.classList.add('hidden');
        }
    } catch (error) {
        resultsDiv.classList.remove('hidden');
        resultsDiv.innerHTML = `
            <div class="card fade-in">
                <div class="card-body">
                    <p style="color:var(--color-danger);text-align:center;padding:20px;">
                        <i class="fas fa-exclamation-circle" style="font-size:2rem;display:block;margin-bottom:12px;"></i>
                        ${getErrorMessage(error)}
                    </p>
                </div>
            </div>
        `;
        stockInfoDiv.classList.add('hidden');
    } finally {
        hideLoading();
    }
}

// =============================================================================
// Company Info
// =============================================================================

async function fetchCompanyInfo(symbol) {
    try {
        const response = await stocksApi.getCompany(symbol);
        const companyDiv = document.getElementById('companyInfo');

        if (response.success && response.data) {
            const c = response.data;
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
    } catch (error) {
        document.getElementById('companyInfo').innerHTML =
            `<p class="text-muted">Company info unavailable: ${getErrorMessage(error)}</p>`;
    }
}

// =============================================================================
// Current Quote
// =============================================================================

async function fetchQuote(symbol) {
    try {
        const response = await stocksApi.getQuote(symbol);
        const quoteDiv = document.getElementById('quoteInfo');

        if (response.success && response.data) {
            const q = response.data;
            const changeClass = q.change >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = q.change >= 0 ? 'fa-caret-up' : 'fa-caret-down';

            quoteDiv.innerHTML = `
                <div style="text-align:center;padding:16px 0;">
                    <p style="font-size:0.8rem;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">
                        ${q.symbol || symbol}
                    </p>
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
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('quoteInfo').innerHTML =
            `<p class="text-muted">Quote unavailable: ${getErrorMessage(error)}</p>`;
    }
}

// =============================================================================
// Navigate to Stock Detail Page
// =============================================================================

function navigateToStock(symbol) {
    window.location.href = `stock.html?symbol=${symbol}`;
}