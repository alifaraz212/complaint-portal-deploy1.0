if (redirectIfNotAuthenticated()) throw new Error('Not authenticated');

setTextSafe('userEmail', getUserEmail());

const statusColors = {
    'open': 'badge-open',
    'in_progress': 'badge-in_progress',
    'resolved': 'badge-resolved',
    'closed': 'badge-closed'
};

let currentPage = 1;
let currentStatus = '';

async function loadComplaints(page = 1, status = '') {
    const tbody = document.getElementById('complaintsTable');
    tbody.innerHTML = '';

    try {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        params.append('page', page);

        const data = await apiRequest(`/complaints/complaints/?${params.toString()}`);
        const complaints = data.results || data;
        const count = data.count || complaints.length;
        const pageSize = 10;

        if (!complaints.length) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 6;
            td.className = 'empty';
            td.textContent = 'No complaints found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            renderPagination(0, pageSize, page);
            return;
        }

        complaints.forEach(complaint => {
            const tr = document.createElement('tr');

            const tdId = document.createElement('td');
            tdId.textContent = complaint.complaint_number; // SAFE

            const tdSubject = document.createElement('td');
            tdSubject.textContent = complaint.subject; // SAFE

            const tdCategory = document.createElement('td');
            tdCategory.textContent = complaint.category_name || '-'; // SAFE

            const tdStatus = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = `badge ${statusColors[complaint.status] || ''}`;
            badge.textContent = complaint.status.replace('_', ' ').toUpperCase(); // SAFE
            tdStatus.appendChild(badge);

            const tdDate = document.createElement('td');
            tdDate.textContent = new Date(complaint.created_at).toLocaleDateString(); // SAFE

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

        renderPagination(count, pageSize, page);

    } catch (error) {
        showError(error.message);
    }
}

function renderPagination(total, pageSize, current) {
    const container = document.getElementById('pagination');
    container.innerHTML = '';
    const totalPages = Math.ceil(total / pageSize);
    if (totalPages <= 1) return;

    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.textContent = '← Prev';
    prevBtn.disabled = current === 1;
    prevBtn.addEventListener('click', () => {
        currentPage = current - 1;
        loadComplaints(currentPage, currentStatus);
    });
    container.appendChild(prevBtn);

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.className = `page-btn${i === current ? ' active' : ''}`;
        btn.textContent = i;
        const pageNum = i;
        btn.addEventListener('click', () => {
            currentPage = pageNum;
            loadComplaints(currentPage, currentStatus);
        });
        container.appendChild(btn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = current === totalPages;
    nextBtn.addEventListener('click', () => {
        currentPage = current + 1;
        loadComplaints(currentPage, currentStatus);
    });
    container.appendChild(nextBtn);
}

document.getElementById('statusFilter').addEventListener('change', (e) => {
    currentStatus = e.target.value;
    currentPage = 1;
    loadComplaints(currentPage, currentStatus);
});

loadComplaints(1, '');
