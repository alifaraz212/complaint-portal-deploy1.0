document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('http://localhost:8000/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            // Our custom exception handler uses {error: "...", details: {...}}
            // DRF default uses {detail: "..."}
            throw new Error(error.error || error.detail || 'Login failed');
        }

        const data = await response.json();
        saveTokens(data.access, data.refresh);

        // Redirect based on role decoded from JWT
        const role = getUserRole();
        if (role === 'admin') {
            window.location.href = '/admin-dashboard.html';
        } else {
            window.location.href = '/user-dashboard.html';
        }
    } catch (error) {
        showError(error.message);
    }
});
