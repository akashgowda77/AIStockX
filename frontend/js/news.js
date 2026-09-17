/**
 * AIStockX - News & FinBERT Sentiment Module
 */

'use strict';

let currentNewsData = null;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initAuthenticatedPage('news');
    loadNewsPage();
});

async function loadNewsPage() {
    const input = document.getElementById('newsSymbolInput');
    if (!input) return;

    const symbol = input.value.trim().toUpperCase() || 'AAPL';
    document.getElementById('newsSymbolInput').value = symbol;

    const loading = document.getElementById('newsLoading');
    const content = document.getElementById('newsContent');

    if (loading) loading.classList.remove('hidden');
    if (content) content.classList.add('hidden');

    try {
        const res = await newsApi.getSentiment(symbol, 15);
        currentNewsData = res;

        if (loading) loading.classList.add('hidden');
        if (content) content.classList.remove('hidden');

        renderNewsOverview(res);
        renderNewsFeed(res ? res.news : []);
    } catch (err) {
        if (loading) loading.classList.add('hidden');
        if (content) content.classList.remove('hidden');
        showToast(`Failed to load news for ${symbol}`, 'error');
    }
}

function selectNewsSymbol(symbol, btn) {
    document.querySelectorAll('#stockChips button').forEach(b => b.classList.remove('active-chip'));
    if (btn) btn.classList.add('active-chip');
    const input = document.getElementById('newsSymbolInput');
    if (input) {
        input.value = symbol;
        loadNewsPage();
    }
}

function renderNewsOverview(data) {
    if (!data) return;

    const symbolHeader = document.getElementById('newsSymbolHeader');
    if (symbolHeader) symbolHeader.textContent = data.symbol || 'Stock';

    const score = data.overall_sentiment_score || 0.0;
    const label = data.overall_sentiment_label || 'Neutral';
    const dist = data.sentiment_distribution || { bullish: 0, neutral: 0, bearish: 0 };
    const total = (dist.bullish + dist.neutral + dist.bearish) || 1;

    const scoreEl = document.getElementById('newsOverallScore');
    const badgeEl = document.getElementById('newsOverallBadge');

    if (scoreEl) {
        scoreEl.textContent = (score >= 0 ? '+' : '') + score.toFixed(2);
        scoreEl.style.color = score >= 0.15 ? '#10b981' : (score <= -0.15 ? '#ef4444' : '#9ca3af');
    }

    if (badgeEl) {
        badgeEl.textContent = label;
        badgeEl.className = `badge ${label === 'Bullish' ? 'badge-success' : (label === 'Bearish' ? 'badge-danger' : 'badge-info')}`;
    }

    const gBull = document.getElementById('newsGaugeBullish');
    const gNeu = document.getElementById('newsGaugeNeutral');
    const gBear = document.getElementById('newsGaugeBearish');

    if (gBull) gBull.style.width = `${((dist.bullish / total) * 100).toFixed(1)}%`;
    if (gNeu) gNeu.style.width = `${((dist.neutral / total) * 100).toFixed(1)}%`;
    if (gBear) gBear.style.width = `${((dist.bearish / total) * 100).toFixed(1)}%`;

    const cBull = document.getElementById('newsCountBullish');
    const cNeu = document.getElementById('newsCountNeutral');
    const cBear = document.getElementById('newsCountBearish');

    if (cBull) cBull.textContent = dist.bullish;
    if (cNeu) cNeu.textContent = dist.neutral;
    if (cBear) cBear.textContent = dist.bearish;
}

function filterNews(label, btn) {
    currentFilter = label;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    if (currentNewsData && currentNewsData.news) {
        let filtered = currentNewsData.news;
        if (label !== 'all') {
            filtered = currentNewsData.news.filter(n => n.sentiment_label === label);
        }
        renderNewsFeed(filtered);
    }
}

function renderNewsFeed(news) {
    const feed = document.getElementById('newsFeedList');
    if (!feed) return;

    if (!news || news.length === 0) {
        feed.innerHTML = `<p style="text-align:center;color:var(--color-text-muted);padding:30px;">No news headlines found matching this filter.</p>`;
        return;
    }

    feed.innerHTML = news.map(item => {
        const itemScore = item.sentiment_score || 0.0;
        const itemLabel = item.sentiment_label || 'Neutral';
        const badgeClass = itemLabel === 'Bullish' ? 'badge-success' : (itemLabel === 'Bearish' ? 'badge-danger' : 'badge-info');
        const dateStr = item.datetime ? new Date(item.datetime).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recent';

        return `
            <div class="news-item-card" style="padding:16px 20px;background:var(--color-bg);border-radius:var(--radius-md);border:1px solid rgba(255,255,255,0.05);display:flex;justify-content:space-between;align-items:flex-start;gap:20px;transition:transform 0.2s, border-color 0.2s;">
                <div style="flex:1;">
                    <div style="font-size:1.02rem;font-weight:600;margin-bottom:8px;line-height:1.4;">
                        <a href="${item.url}" target="_blank" rel="noopener" style="color:var(--color-text-primary);text-decoration:none;transition:color 0.2s;">
                            ${item.headline} <i class="fas fa-external-link-alt" style="font-size:0.75rem;color:var(--color-text-muted);margin-left:6px;"></i>
                        </a>
                    </div>
                    ${item.summary ? `<p style="font-size:0.88rem;color:var(--color-text-secondary);margin-bottom:10px;line-height:1.5;">${item.summary.substring(0, 180)}...</p>` : ''}
                    <div style="font-size:0.78rem;color:var(--color-text-muted);display:flex;gap:16px;align-items:center;flex-wrap:wrap;">
                        <span><i class="fas fa-building"></i> ${item.source}</span>
                        <span><i class="far fa-clock"></i> ${dateStr}</span>
                        <span><i class="fas fa-microchip"></i> FinBERT Confidence: ${(item.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div style="text-align:right;white-space:nowrap;">
                    <span class="badge ${badgeClass}" style="font-weight:700;font-size:0.85rem;padding:6px 12px;">${itemLabel}</span>
                    <div style="font-size:1rem;font-weight:800;margin-top:8px;color:${itemScore >= 0.15 ? '#10b981' : (itemScore <= -0.15 ? '#ef4444' : '#9ca3af')};">
                        ${(itemScore >= 0 ? '+' : '') + itemScore.toFixed(2)}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}
