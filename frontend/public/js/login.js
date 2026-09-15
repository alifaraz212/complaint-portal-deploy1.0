document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    try {
        const data = await apiRequest('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

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
