/**
 * AIStockX - Storage Module
 * Single responsibility: JWT token, user profile, selected stock persistence
 */

const STORAGE_KEYS = {
    TOKEN: 'aistockx_token',
    USER: 'aistockx_user',
    SELECTED_STOCK: 'aistockx_selected_stock',
};

// =============================================================================
// Token Management
// =============================================================================

function getToken() {
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
}

function setToken(token) {
    localStorage.setItem(STORAGE_KEYS.TOKEN, token);
}

function removeToken() {
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
}

function hasToken() {
    return !!getToken();
}

// =============================================================================
// User Profile Management
// =============================================================================

function getUser() {
    try {
        const data = localStorage.getItem(STORAGE_KEYS.USER);
        return data ? JSON.parse(data) : null;
    } catch {
        return null;
    }
}

function setUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
}

function removeUser() {
    localStorage.removeItem(STORAGE_KEYS.USER);
}

// =============================================================================
// Selected Stock
// =============================================================================

function getSelectedStock() {
    try {
        const data = localStorage.getItem(STORAGE_KEYS.SELECTED_STOCK);
        return data ? JSON.parse(data) : null;
    } catch {
        return null;
    }
}

function setSelectedStock(stock) {
    localStorage.setItem(STORAGE_KEYS.SELECTED_STOCK, JSON.stringify(stock));
}

function removeSelectedStock() {
    localStorage.removeItem(STORAGE_KEYS.SELECTED_STOCK);
}

// =============================================================================
// Clear All
// =============================================================================

function clearAll() {
    removeToken();
    removeUser();
    removeSelectedStock();
}

// =============================================================================
// Auth State Check
// =============================================================================

function isAuthenticated() {
    return hasToken();
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = 'dashboard.html';
        return true;
    }
    return false;
}