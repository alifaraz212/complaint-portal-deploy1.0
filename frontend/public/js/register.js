document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const full_name = document.getElementById('full_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const password = document.getElementById('password').value;
    const password_confirm = document.getElementById('password_confirm').value;

    // Client-side validation
    if (password !== password_confirm) {
        showError('Passwords do not match');
        return;
    }

    if (password.length < 8) {
        showError('Password must be at least 8 characters');
        return;
    }

    // Phone validation (optional field)
    if (phone) {
        if (!/^[0-9+\-\s()]+$/.test(phone)) {
            showError('Phone number can only contain digits, +, -, spaces, and parentheses');
            return;
        }
        const digitsOnly = phone.replace(/\D/g, '');
        if (digitsOnly.length < 7) {
            showError('Phone number is too short (minimum 7 digits)');
            return;
        }
    }

    try {
        const response = await fetch('http://localhost:8000/api/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Backend expects only these 4 fields (no password_confirm)
            body: JSON.stringify({ full_name, email, phone, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || JSON.stringify(error));
        }

        showSuccess('Registration successful! Please login.');
        window.location.href = '/login.html';
    } catch (error) {
        showError(error.message);
    }
});
