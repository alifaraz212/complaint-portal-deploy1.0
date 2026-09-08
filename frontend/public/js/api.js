// API Request Wrapper with Auto-Refresh
// Security: Uses _retry flag to prevent infinite refresh loops

const API_BASE_URL = 'http://localhost:8000/api';

async function apiRequest(url, options = {}) {
    let token = getAccessToken();
    
    const config = {
        ...options,
        headers: {
            ...options.headers,
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };

    // If body is not FormData, set Content-Type to JSON
    if (config.body && !(config.body instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json';
    }

    let response = await fetch(`${API_BASE_URL}${url}`, config);

    // If 401 and haven't retried yet, refresh token and retry once
    if (response.status === 401 && !options._retry) {
        const newToken = await refreshAccessToken();
        if (newToken) {
            // Retry with _retry flag to prevent infinite loop
            return apiRequest(url, { ...options, _retry: true });
        } else {
            throw new Error('Authentication failed');
        }
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || error.message || JSON.stringify(error));
    }

    return response.json();
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert(message);
}

// XSS-safe helper to create elements with text content
function createElementWithText(tag, text, className = '') {
    const el = document.createElement(tag);
    el.textContent = text; // SAFE: textContent prevents XSS
    if (className) el.className = className;
    return el;
}

// XSS-safe helper to set text content
function setTextSafe(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text; // SAFE: textContent prevents XSS
}
