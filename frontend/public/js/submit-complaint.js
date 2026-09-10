if (redirectIfNotAuthenticated()) throw new Error('Not authenticated');

async function loadCategories() {
    try {
        const categories = await apiRequest('/complaints/categories/');
        const select = document.getElementById('category');

        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name; // SAFE: textContent
            select.appendChild(option);
        });
    } catch (error) {
        showError('Failed to load categories: ' + error.message);
    }
}

document.getElementById('complaintForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const category = document.getElementById('category').value;
    const subject = document.getElementById('subject').value.trim();
    const description = document.getElementById('description').value.trim();
    const attachmentFile = document.getElementById('attachment').files[0];

    if (!category) {
        showError('Please select a category');
        return;
    }

    try {
        // Step 1: Create complaint (JSON, no attachment)
        const complaint = await apiRequest('/complaints/complaints/', {
            method: 'POST',
            body: JSON.stringify({ category: parseInt(category), subject, description })
        });

        // Step 2: Upload attachment if selected
        if (attachmentFile) {
            const formData = new FormData();
            formData.append('file', attachmentFile);

            try {
                await apiRequest(`/complaints/complaints/${complaint.id}/attachments/`, {
                    method: 'POST',
                    body: formData
                });
            } catch (attachErr) {
                // Complaint was created but attachment failed — still redirect
                showError('Complaint submitted but attachment upload failed: ' + attachErr.message);
                window.location.href = '/user-dashboard.html';
                return;
            }
        }

        showSuccess('Complaint submitted successfully!');
        window.location.href = '/user-dashboard.html';

    } catch (error) {
        showError(error.message);
    }
});

loadCategories();
