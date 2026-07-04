/**
 * AIStockX - Utility Functions
 * Single responsibility: formatting, validation, loading, toast, helpers
 */

// =============================================================================
// Toast Notification System
// =============================================================================

function showToast(message, type = 'success', duration = 3500) {
    const existing = document.querySelector('.toast-container');
    if (existing) existing.remove();

    const container = document.createElement('div');
    container.className = 'toast-container';
    container.innerHTML = `
        <div class="toast toast-${type}">
            <div class="toast-icon">
                ${type === 'success' ? '<i class="fas fa-check-circle"></i>' : ''}
                ${type === 'error' ? '<i class="fas fa-exclamation-circle"></i>' : ''}
                ${type === 'info' ? '<i class="fas fa-info-circle"></i>' : ''}
                ${type === 'warning' ? '<i class="fas fa-exclamation-triangle"></i>' : ''}
            </div>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    document.body.appendChild(container);

    setTimeout(() => {
        if (container.parentElement) {
            container.style.opacity = '0';
            container.style.transform = 'translateX(100%)';
            setTimeout(() => container.remove(), 300);
        }
    }, duration);
}

// =============================================================================
// Loading Spinner
// =============================================================================

function showLoading(containerId = null) {
    const target = containerId ? document.getElementById(containerId) : document.body;
    if (!target) return;

    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'global-loading';
    overlay.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-ring"></div>
            <p class="loading-text">Loading...</p>
        </div>
    `;
    target.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('global-loading');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    }
}

// =============================================================================
// Form Validation
// =============================================================================

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(password)) return 'Password must contain an uppercase letter';
    if (!/[0-9]/.test(password)) return 'Password must contain a number';
    return null;
}

function validateUsername(username) {
    if (username.trim().length < 3) return 'Username must be at least 3 characters';
    return null;
}

// =============================================================================
// Number Formatting
// =============================================================================

function formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value);
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value);
}

function formatPercent(value) {
    if (value === null || value === undefined) return '—';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${formatNumber(value, 2)}%`;
}

function formatCompactNumber(value) {
    if (value === null || value === undefined) return '—';
    if (value >= 1e12) return (value / 1e12).toFixed(2) + 'T';
    if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B';
    if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M';
    if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K';
    return value.toFixed(2);
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

// =============================================================================
// DOM Helpers
// =============================================================================

function $(selector, parent = document) {
    return parent.querySelector(selector);
}

function $$(selector, parent = document) {
    return parent.querySelectorAll(selector);
}

function createElement(tag, className = '', innerHTML = '') {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (innerHTML) el.innerHTML = innerHTML;
    return el;
}

// =============================================================================
// Error Handling
// =============================================================================

function getErrorMessage(error) {
    if (typeof error === 'string') return error;
    if (error?.detail) return error.detail;
    if (error?.message) return error.message;
    return 'An unexpected error occurred';
}

// =============================================================================
// Change Color Helper
// =============================================================================

function getChangeColor(value) {
    if (value === null || value === undefined) return '';
    return value >= 0 ? 'text-success' : 'text-danger';
}

function getChangeIcon(value) {
    if (value === null || value === undefined) return '';
    return value >= 0 ? 'fa-caret-up' : 'fa-caret-down';
}