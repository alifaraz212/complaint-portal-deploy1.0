if (redirectIfNotAuthenticated()) throw new Error('Not authenticated');

// Set user email in navbar
setTextSafe('userEmail', getUserEmail());

const statusColors = {
    'open': 'badge-open',
    'in_progress': 'badge-in_progress',
    'resolved': 'badge-resolved',
    'closed': 'badge-closed'
};

async function loadComplaints(status = '') {
    const tbody = document.getElementById('complaintsTable');
    tbody.innerHTML = '';

    try {
        const url = status ? `/complaints/complaints/?status=${status}` : '/complaints/complaints/';
        const data = await apiRequest(url);

        // Handle paginated response
        const complaints = data.results || data;

        if (!complaints.length) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 6;
            td.className = 'empty';
            td.textContent = 'No complaints found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        complaints.forEach(complaint => {
            const tr = document.createElement('tr');

            // ID
            const tdId = document.createElement('td');
            tdId.textContent = complaint.complaint_number;

            // Subject
            const tdSubject = document.createElement('td');
            tdSubject.textContent = complaint.subject;

            // Category
            const tdCategory = document.createElement('td');
            tdCategory.textContent = complaint.category_name || '-';

            // Status badge
            const tdStatus = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = `badge ${statusColors[complaint.status] || ''}`;
            badge.textContent = complaint.status.replace('_', ' ').toUpperCase();
            tdStatus.appendChild(badge);

            // Created at
            const tdDate = document.createElement('td');
            tdDate.textContent = new Date(complaint.created_at).toLocaleDateString();

            // View link
            const tdAction = document.createElement('td');
            const link = document.createElement('a');
            link.href = `/complaint-detail.html?id=${complaint.id}`;
            link.className = 'link';
            link.textContent = 'View';
            tdAction.appendChild(link);

            tr.appendChild(tdId);
            tr.appendChild(tdSubject);
            tr.appendChild(tdCategory);
            tr.appendChild(tdStatus);
            tr.appendChild(tdDate);
            tr.appendChild(tdAction);
            tbody.appendChild(tr);
        });

    } catch (error) {
        showError(error.message);
    }
}

document.getElementById('statusFilter').addEventListener('change', (e) => {
    loadComplaints(e.target.value);
});

loadComplaints();
