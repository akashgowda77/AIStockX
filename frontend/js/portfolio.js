/**
 * AIStockX - Virtual Portfolio Simulator Module
 * Handles simulated trading ($10,000 wallet), holdings, performance charts & transaction log.
 */

'use strict';

let currentTradeAction = 'BUY';
let selectedSymbolQuote = null;
let allocationChartInstance = null;

// Self-healing fallback definition for portfolioApi if missing due to stale browser cache
if (typeof portfolioApi === 'undefined' && typeof request === 'function') {
    window.portfolioApi = {
        getSummary() {
            return request('/api/portfolio', { auth: true });
        },
        trade(symbol, action, quantity) {
            return request('/api/portfolio/trade', {
                method: 'POST',
                auth: true,
                body: { symbol, action, quantity: Number(quantity) }
            });
        },
        getTransactions() {
            return request('/api/portfolio/transactions', { auth: true });
        },
        reset() {
            return request('/api/portfolio/reset', { method: 'POST', auth: true });
        },
    };
}

document.addEventListener('DOMContentLoaded', () => {
    initAuthenticatedPage('portfolio');
    initPortfolioPage();
});

async function initPortfolioPage() {
    setupTradeEventListeners();
    await refreshPortfolio();
    // Default preview symbol
    fetchSymbolQuote('INFY');
}

function setupTradeEventListeners() {
    const symbolInput = document.getElementById('tradeSymbolInput');
    const qtyInput = document.getElementById('tradeQuantityInput');

    if (symbolInput) {
        symbolInput.addEventListener('change', () => {
            const sym = symbolInput.value.trim().toUpperCase();
            if (sym) fetchSymbolQuote(sym);
        });
    }

    if (qtyInput) {
        qtyInput.addEventListener('input', calculateEstimatedCost);
    }
}

function setTradeAction(action) {
    currentTradeAction = action;
    const buyBtn = document.getElementById('btnTradeActionBuy');
    const sellBtn = document.getElementById('btnTradeActionSell');
    const submitBtn = document.getElementById('btnSubmitTrade');

    if (action === 'BUY') {
        buyBtn.classList.add('active', 'buy');
        sellBtn.classList.remove('active', 'sell');
        submitBtn.className = 'btn-execute-trade buy';
        submitBtn.innerHTML = '<i class="fas fa-shopping-cart"></i> Execute Buy Trade';
    } else {
        sellBtn.classList.add('active', 'sell');
        buyBtn.classList.remove('active', 'buy');
        submitBtn.className = 'btn-execute-trade sell';
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Execute Sell Trade';
    }
    calculateEstimatedCost();
}

async function fetchSymbolQuote(symbol) {
    symbol = symbol.toUpperCase();
    const previewContainer = document.getElementById('symbolQuotePreview');
    if (!previewContainer) return;

    previewContainer.innerHTML = '<div class="text-muted"><i class="fas fa-spinner fa-spin"></i> Fetching quote for ' + symbol + '...</div>';

    try {
        const response = await (window.stocksApi || window.stockApi).getQuote(symbol);
        const quote = (response && response.data) ? response.data : response;
        selectedSymbolQuote = quote;

        const symbolInput = document.getElementById('tradeSymbolInput');
        if (symbolInput) symbolInput.value = symbol;

        const price = quote.price !== undefined ? quote.price : (quote.c || 0);
        const change = quote.change !== undefined ? quote.change : (quote.d || 0);
        const pctChange = quote.percent_change !== undefined ? quote.percent_change : (quote.dp || 0);
        const isPos = change >= 0;

        // Fetch AI recommendation if available
        let aiBadgeHtml = '<span class="ai-recommendation-badge badge-ai-hold"><i class="fas fa-robot"></i> AI Signal: HOLD</span>';
        try {
            const predRes = await (window.predictionsApi || window.predictionApi).predictLinear(symbol);
            const predData = (predRes && predRes.data) ? predRes.data : predRes;
            if (predData && predData.prediction) {
                const predPrice = predData.prediction.predicted_price;
                const retPct = price > 0 ? (((predPrice - price) / price) * 100) : 0;

                if (retPct > 2.0) {
                    aiBadgeHtml = `<span class="ai-recommendation-badge badge-ai-buy"><i class="fas fa-arrow-up"></i> AI Signal: BUY (+${retPct.toFixed(1)}%)</span>`;
                } else if (retPct < -2.0) {
                    aiBadgeHtml = `<span class="ai-recommendation-badge badge-ai-sell"><i class="fas fa-arrow-down"></i> AI Signal: SELL (${retPct.toFixed(1)}%)</span>`;
                } else {
                    aiBadgeHtml = `<span class="ai-recommendation-badge badge-ai-hold"><i class="fas fa-minus"></i> AI Signal: HOLD (${retPct >= 0 ? '+' : ''}${retPct.toFixed(1)}%)</span>`;
                }
            }
        } catch {
            // Default HOLD badge if prediction endpoint fails
        }

        previewContainer.innerHTML = `
            <div class="quote-preview-header">
                <div>
                    <strong style="font-size: 1.1rem; color: var(--color-text-primary);">${symbol}</strong>
                    <span style="font-size: 1.2rem; font-weight: 700; margin-left: 10px;">$${price.toFixed(2)}</span>
                    <span style="font-size: 0.85rem; font-weight: 600; color: ${isPos ? '#10b981' : '#ef4444'}; margin-left: 6px;">
                        ${isPos ? '+' : ''}${change.toFixed(2)} (${isPos ? '+' : ''}${pctChange.toFixed(2)}%)
                    </span>
                </div>
                <div>${aiBadgeHtml}</div>
            </div>
        `;

        calculateEstimatedCost();
    } catch (err) {
        selectedSymbolQuote = null;
        previewContainer.innerHTML = `<div style="color: #ef4444;"><i class="fas fa-exclamation-circle"></i> Unable to load live quote for '${symbol}'.</div>`;
        document.getElementById('estimatedTotalCost').textContent = '$0.00';
    }
}

function calculateEstimatedCost() {
    const qtyInput = document.getElementById('tradeQuantityInput');
    const costDisplay = document.getElementById('estimatedTotalCost');
    if (!qtyInput || !costDisplay) return;

    const qty = parseFloat(qtyInput.value) || 0;
    const price = selectedSymbolQuote ? (selectedSymbolQuote.price !== undefined ? selectedSymbolQuote.price : (selectedSymbolQuote.c || 0)) : 0;
    const total = qty * price;

    costDisplay.textContent = `$${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

async function handleTradeSubmit(event) {
    event.preventDefault();

    const symbolInput = document.getElementById('tradeSymbolInput');
    const qtyInput = document.getElementById('tradeQuantityInput');

    const symbol = symbolInput ? symbolInput.value.trim().toUpperCase() : '';
    const qty = qtyInput ? parseFloat(qtyInput.value) : 0;

    if (!symbol) {
        showToast('Please enter a stock symbol.', 'error');
        return;
    }
    if (!qty || qty <= 0) {
        showToast('Please enter a valid share quantity.', 'error');
        return;
    }

    const submitBtn = document.getElementById('btnSubmitTrade');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing Trade...';

    try {
        const response = await portfolioApi.trade(symbol, currentTradeAction, qty);
        showToast(response.message, 'success');
        await refreshPortfolio();
        if (qtyInput) qtyInput.value = '1';
        calculateEstimatedCost();
    } catch (err) {
        showToast(err.message || 'Trade execution failed.', 'error');
    } finally {
        submitBtn.disabled = false;
        setTradeAction(currentTradeAction);
    }
}

async function refreshPortfolio() {
    try {
        const summary = await portfolioApi.getSummary();
        renderStatCards(summary);
        renderHoldingsTable(summary.holdings);
        renderAllocationChart(summary);

        const txList = await portfolioApi.getTransactions();
        renderTransactionTable(txList);
    } catch (err) {
        console.error('Failed to load portfolio:', err);
    }
}

function renderStatCards(summary) {
    const netWorth = document.getElementById('valNetWorth');
    const cashBal = document.getElementById('valCashBalance');
    const holdingsVal = document.getElementById('valHoldingsValue');
    const totalPnl = document.getElementById('valTotalPnl');

    if (netWorth) netWorth.textContent = `$${summary.total_portfolio_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (cashBal) cashBal.textContent = `$${summary.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (holdingsVal) holdingsVal.textContent = `$${summary.total_stock_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

    if (totalPnl) {
        const isPos = summary.total_profit_loss >= 0;
        totalPnl.className = `stat-card-val ${isPos ? 'stat-pnl-positive' : 'stat-pnl-negative'}`;
        totalPnl.textContent = `${isPos ? '+' : ''}$${summary.total_profit_loss.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${isPos ? '+' : ''}${summary.total_profit_loss_pct.toFixed(2)}%)`;
    }
}

function renderHoldingsTable(holdings) {
    const tbody = document.getElementById('holdingsTableBody');
    if (!tbody) return;

    if (!holdings || holdings.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--color-text-muted); padding: 32px;">
                    <i class="fas fa-folder-open" style="font-size: 2rem; margin-bottom: 8px; display: block;"></i>
                    No stock holdings yet. Use the Trade Execution panel to buy your first stock!
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = holdings.map(h => {
        const isPos = h.profit_loss >= 0;
        let aiBadge = '<span class="ai-recommendation-badge badge-ai-hold">HOLD</span>';
        if (h.ai_recommendation === 'BUY') {
            aiBadge = `<span class="ai-recommendation-badge badge-ai-buy">BUY (+${h.ai_predicted_return_pct}%)</span>`;
        } else if (h.ai_recommendation === 'SELL') {
            aiBadge = `<span class="ai-recommendation-badge badge-ai-sell">SELL (${h.ai_predicted_return_pct}%)</span>`;
        }

        return `
            <tr>
                <td><strong>${h.symbol}</strong></td>
                <td>${h.quantity}</td>
                <td>$${h.average_buy_price.toFixed(2)}</td>
                <td>$${h.current_price.toFixed(2)}</td>
                <td>$${h.total_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                <td style="font-weight: 600; color: ${isPos ? '#10b981' : '#ef4444'};">
                    ${isPos ? '+' : ''}$${h.profit_loss.toFixed(2)} (${isPos ? '+' : ''}${h.profit_loss_pct.toFixed(2)}%)
                </td>
                <td>${aiBadge}</td>
                <td>
                    <button class="btn-quick-action btn-quick-buy" onclick="quickTrade('${h.symbol}', 'BUY')"><i class="fas fa-plus"></i> Buy</button>
                    <button class="btn-quick-action btn-quick-sell" onclick="quickTrade('${h.symbol}', 'SELL')"><i class="fas fa-minus"></i> Sell</button>
                </td>
            </tr>
        `;
    }).join('');
}

function quickTrade(symbol, action) {
    document.getElementById('tradeSymbolInput').value = symbol;
    setTradeAction(action);
    fetchSymbolQuote(symbol);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderAllocationChart(summary) {
    const canvas = document.getElementById('allocationChart');
    if (!canvas) return;

    const labels = ['Cash Balance'];
    const data = [summary.cash_balance];
    const colors = ['#10b981'];

    const stockColors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#06b6d4', '#6366f1'];

    summary.holdings.forEach((h, index) => {
        labels.push(h.symbol);
        data.push(h.total_value);
        colors.push(stockColors[index % stockColors.length]);
    });

    if (allocationChartInstance) {
        allocationChartInstance.destroy();
    }

    allocationChartInstance = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, padding: 14 }
                }
            }
        }
    });
}

function renderTransactionTable(transactions) {
    const tbody = document.getElementById('transactionTableBody');
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: var(--color-text-muted); padding: 24px;">
                    No transactions recorded yet.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = transactions.map(tx => {
        const isBuy = tx.transaction_type === 'BUY';
        const dateStr = new Date(tx.timestamp).toLocaleString();

        return `
            <tr>
                <td><small>${dateStr}</small></td>
                <td><strong>${tx.symbol}</strong></td>
                <td>
                    <span style="font-weight: 700; color: ${isBuy ? '#10b981' : '#ef4444'};">
                        <i class="fas ${isBuy ? 'fa-arrow-down' : 'fa-arrow-up'}"></i> ${tx.transaction_type}
                    </span>
                </td>
                <td>${tx.quantity}</td>
                <td>$${tx.price_per_share.toFixed(2)}</td>
                <td><strong>$${tx.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong></td>
            </tr>
        `;
    }).join('');
}

async function confirmResetPortfolio() {
    if (!confirm("Are you sure you want to reset your virtual portfolio?\n\nThis will reset your cash balance back to $10,000.00 and delete all holdings & trade history.")) {
        return;
    }

    try {
        const res = await portfolioApi.reset();
        showToast(res.message, 'info');
        await refreshPortfolio();
    } catch (err) {
        showToast(err.message || 'Reset failed.', 'error');
    }
}
