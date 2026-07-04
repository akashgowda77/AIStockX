/**
 * AIStockX - Charts Module
 * Single responsibility: All Chart.js chart creation and management
 * No fetch() calls or business logic here.
 */

// =============================================================================
// Chart Defaults
// =============================================================================

Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#9aa0a6';
Chart.defaults.borderColor = 'rgba(0,0,0,0.06)';

// =============================================================================
// Utility: Create gradient
// =============================================================================

function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

// =============================================================================
// Price Line Chart
// =============================================================================

function createPriceChart(canvasId, labels, prices, color = '#1a73e8') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');
    const gradient = createGradient(ctx, color + '33', color + '00');

    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Close Price',
                data: prices,
                borderColor: color,
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHitRadius: 10,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: color,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1b1f2e',
                    titleColor: '#fff',
                    bodyColor: '#a0a5b5',
                    borderColor: 'rgba(255,255,255,0.06)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(ctx) {
                            return '$' + ctx.parsed.y.toFixed(2);
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        maxRotation: 0,
                    },
                },
                y: {
                    grid: {
                        color: 'rgba(0,0,0,0.04)',
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        },
                    },
                },
            },
        },
    };

    return new Chart(ctx, config);
}

// =============================================================================
// Volume Bar Chart
// =============================================================================

function createVolumeChart(canvasId, labels, volumes) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');

    const config = {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: 'rgba(26, 115, 232, 0.3)',
                borderColor: 'rgba(26, 115, 232, 0.5)',
                borderWidth: 1,
                borderRadius: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1b1f2e',
                    titleColor: '#fff',
                    bodyColor: '#a0a5b5',
                    borderColor: 'rgba(255,255,255,0.06)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(ctx) {
                            return formatCompactNumber(ctx.parsed.y);
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 10,
                        maxRotation: 0,
                    },
                },
                y: {
                    grid: {
                        color: 'rgba(0,0,0,0.04)',
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCompactNumber(value);
                        },
                    },
                },
            },
        },
    };

    return new Chart(ctx, config);
}

// =============================================================================
// Indicator Chart (RSI, MACD, etc.)
// =============================================================================

function createIndicatorChart(canvasId, labels, data, label, color = '#1a73e8', type = 'line') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');

    const config = {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: type === 'bar' ? color + '66' : color + '22',
                borderWidth: type === 'line' ? 2 : 1,
                fill: type === 'line',
                tension: 0.3,
                pointRadius: 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1b1f2e',
                    titleColor: '#fff',
                    bodyColor: '#a0a5b5',
                    borderColor: 'rgba(255,255,255,0.06)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 8,
                        maxRotation: 0,
                    },
                },
                y: {
                    grid: {
                        color: 'rgba(0,0,0,0.04)',
                    },
                },
            },
        },
    };

    return new Chart(ctx, config);
}

// =============================================================================
// Comparison Bar Chart
// =============================================================================

function createComparisonChart(canvasId, labels, datasets) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');

    const config = {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets.map(ds => ({
                label: ds.label,
                data: ds.data,
                backgroundColor: ds.color || '#1a73e8',
                borderColor: ds.borderColor || ds.color || '#1a73e8',
                borderWidth: 1,
                borderRadius: 4,
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 16,
                        font: { size: 12 },
                    },
                },
                tooltip: {
                    backgroundColor: '#1b1f2e',
                    titleColor: '#fff',
                    bodyColor: '#a0a5b5',
                    borderColor: 'rgba(255,255,255,0.06)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                },
                y: {
                    grid: {
                        color: 'rgba(0,0,0,0.04)',
                    },
                    beginAtZero: true,
                },
            },
        },
    };

    return new Chart(ctx, config);
}

// =============================================================================
// Radar Chart for Model Comparison
// =============================================================================

function createRadarChart(canvasId, labels, datasets) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');

    const config = {
        type: 'radar',
        data: {
            labels: labels,
            datasets: datasets.map(ds => ({
                label: ds.label,
                data: ds.data,
                backgroundColor: ds.backgroundColor || ds.color + '33' || 'rgba(26, 115, 232, 0.2)',
                borderColor: ds.color || '#1a73e8',
                borderWidth: 2,
                pointBackgroundColor: ds.color || '#1a73e8',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 16,
                        font: { size: 12 },
                    },
                },
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        font: { size: 10 },
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.06)',
                    },
                    angleLines: {
                        color: 'rgba(0,0,0,0.06)',
                    },
                    pointLabels: {
                        font: { size: 11, weight: '600' },
                        color: '#5f6368',
                    },
                },
            },
        },
    };

    return new Chart(ctx, config);
}

// =============================================================================
// Destroy Chart Helper
// =============================================================================

function destroyChart(chartInstance) {
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
}

// =============================================================================
// Window Resize Handler — re-renders all charts on resize
// =============================================================================

let resizeTimeout = null;

function handleChartResize() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Chart.js responsive: true + maintainAspectRatio: false handles most cases.
        // Force resize on all chart canvases to prevent layout issues.
        document.querySelectorAll('canvas').forEach(canvas => {
            const chart = Chart.getChart(canvas);
            if (chart) {
                chart.resize();
            }
        });
    }, 250);
}

window.addEventListener('resize', handleChartResize);
