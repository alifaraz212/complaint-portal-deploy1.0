// JWT Token Management with Shared Refresh Promise
// Security: Shared promise prevents race conditions on token refresh

const TOKEN_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

function saveTokens(access, refresh) {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
}

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
}

function logout() {
    clearTokens();
    window.location.href = '/login.html';
}

function isAuthenticated() {
    return !!getAccessToken();
}

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

function getUserRole() {
    const token = getAccessToken();
    if (!token) return null;
    const payload = parseJwt(token);
    return payload ? payload.role : null;
}

function getUserEmail() {
    const token = getAccessToken();
    if (!token) return null;
    const payload = parseJwt(token);
    return payload ? payload.email : null;
}

function redirectIfNotAuthenticated() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return true;
    }
    return false;
}

function redirectIfNotAdmin() {
    if (redirectIfNotAuthenticated()) return true;
    if (getUserRole() !== 'admin') {
        alert('Access denied. Admin only.');
        window.location.href = '/user-dashboard.html';
        return true;
    }
    return false;
}

// Shared refresh promise - multiple concurrent 401s wait for same refresh
let refreshPromise = null;

async function refreshAccessToken() {
    // If refresh already in progress, return the same promise
    if (refreshPromise) {
        return refreshPromise;
    }
    
    const refresh = getRefreshToken();
    if (!refresh) {
        logout();
        return null;
    }

    // Create shared promise that all concurrent requests will wait for
    refreshPromise = (async () => {
        try {
            const response = await fetch(`${API_URL}/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh })
            });

            if (!response.ok) {
                clearTokens();
                window.location.href = '/login.html';
                return null;
            }

            const data = await response.json();
            localStorage.setItem(TOKEN_KEY, data.access);
            return data.access;
        } catch (error) {
            clearTokens();
            window.location.href = '/login.html';
            return null;
        } finally {
            // Clear promise after completion so next refresh can start fresh
            refreshPromise = null;
        }
    })();

    return refreshPromise;
}
