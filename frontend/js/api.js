/**
 * AIStockX - API Module
 * Single responsibility: ALL backend HTTP requests using native Fetch API
 * No fetch() calls anywhere else in the application.
 */

const API_BASE_URL = 'http://localhost:8000';

// =============================================================================
// Internal Request Helper
// =============================================================================

async function request(endpoint, options = {}) {
    const { method = 'GET', body = null, auth = false, params = null } = options;

    const headers = {
        'Content-Type': 'application/json',
    };

    if (auth) {
        const token = getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }

    let url = `${API_BASE_URL}${endpoint}`;

    if (params) {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                searchParams.append(key, value);
            }
        });
        const qs = searchParams.toString();
        if (qs) url += `?${qs}`;
    }

    const config = {
        method,
        headers,
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
        const error = new Error(data.detail || 'Request failed');
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
}

// =============================================================================
// Auth API
// =============================================================================

const authApi = {
    register(userData) {
        return request('/api/auth/register', {
            method: 'POST',
            body: userData,
        });
    },

    login(username, password) {
        // The backend uses OAuth2PasswordRequestForm which expects form-data
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        return fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        }).then(async (res) => {
            const data = await res.json();
            if (!res.ok) {
                const error = new Error(data.detail || 'Login failed');
                error.status = res.status;
                error.data = data;
                throw error;
            }
            return data;
        });
    },

    getMe() {
        return request('/api/auth/me', { auth: true });
    },
};

// =============================================================================
// Stocks API
// =============================================================================

const stocksApi = {
    search(query) {
        return request('/stocks/search', {
            params: { query },
        });
    },

    getCompany(symbol) {
        return request(`/stocks/company/${symbol}`);
    },

    getHistory(symbol, period = '1y', interval = '1d') {
        return request(`/stocks/history/${symbol}`, {
            params: { period, interval },
        });
    },

    getQuote(symbol) {
        return request(`/stocks/quote/${symbol}`);
    },
};

// =============================================================================
// Indicators API
// =============================================================================

const indicatorsApi = {
    getIndicators(symbol) {
        return request(`/api/indicators/${symbol}`);
    },
};

// =============================================================================
// Predictions API
// =============================================================================

const predictionsApi = {
    trainLinear(symbol, forceRetrain = false) {
        return request(`/api/prediction/linear/train/${symbol}`, {
            method: 'POST',
            params: { force_retrain: forceRetrain },
        });
    },

    predictLinear(symbol) {
        return request(`/api/prediction/linear/${symbol}`);
    },

    trainLSTM(symbol, forceRetrain = false) {
        return request(`/api/prediction/lstm/train/${symbol}`, {
            method: 'POST',
            params: { force_retrain: forceRetrain },
        });
    },

    predictLSTM(symbol) {
        return request(`/api/prediction/lstm/${symbol}`);
    },

    compareModels(symbol) {
        return request(`/api/prediction/compare/${symbol}`);
    },
};

// =============================================================================
// Model Evaluation API
// =============================================================================

const modelsApi = {
    listAll() {
        return request('/api/models');
    },

    getLinearModel(symbol) {
        return request(`/api/models/${symbol}/linear`);
    },

    modelExists(symbol) {
        return request(`/api/models/${symbol}/exists`);
    },
};

// =============================================================================
// Health API
// =============================================================================

const healthApi = {
    check() {
        return request('/health');
    },
};