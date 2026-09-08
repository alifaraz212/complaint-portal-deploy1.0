if (redirectIfNotAdmin()) throw new Error('Not admin');

const statusColors = {
    'open': 'badge-open',
    'in_progress': 'badge-in_progress',
    'resolved': 'badge-resolved',
    'closed': 'badge-closed'
};

const priorityColors = {
    'low': 'badge-low',
    'medium': 'badge-medium',
    'high': 'badge-high',
    'urgent': 'badge-urgent'
};

let currentPage = 1;
let searchTimeout = null;

async function loadCategories() {
    try {
        const categories = await apiRequest('/complaints/categories/');
        const select = document.getElementById('categoryFilter');
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name; // SAFE: textContent
            select.appendChild(option);
        });
    } catch (e) {
        // Non-critical — filters still work without category list
    }
}

async function loadComplaints(page = 1) {
    const search = document.getElementById('searchInput').value.trim();
    const status = document.getElementById('statusFilter').value;
    const priority = document.getElementById('priorityFilter').value;
    const category = document.getElementById('categoryFilter').value;

    // Build query string
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    if (category) params.append('category', category);
    params.append('page', page);

    const tbody = document.getElementById('complaintsTable');
    tbody.innerHTML = '';

    try {
        const data = await apiRequest(`/complaints/complaints/?${params.toString()}`);

        const complaints = data.results || data;
        const count = data.count || complaints.length;
        const pageSize = 10;

        if (!complaints.length) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 8;
            td.className = 'empty';
            td.textContent = 'No complaints found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            renderPagination(0, pageSize, page);
            return;
        }

        complaints.forEach(complaint => {
            const tr = document.createElement('tr');

            // ID
            const tdId = document.createElement('td');
            tdId.textContent = complaint.complaint_number; // SAFE

            // Subject
            const tdSubject = document.createElement('td');
            tdSubject.textContent = complaint.subject; // SAFE

            // User
            const tdUser = document.createElement('td');
            tdUser.textContent = complaint.user_email || '-'; // SAFE

            // Category
            const tdCat = document.createElement('td');
            tdCat.textContent = complaint.category_name || '-'; // SAFE

            // Status
            const tdStatus = document.createElement('td');
            const sBadge = document.createElement('span');
            sBadge.className = `badge ${statusColors[complaint.status] || ''}`;
            sBadge.textContent = complaint.status.replace('_', ' ').toUpperCase(); // SAFE
            tdStatus.appendChild(sBadge);

            // Priority
            const tdPriority = document.createElement('td');
            if (complaint.priority) {
                const pBadge = document.createElement('span');
                pBadge.className = `badge ${priorityColors[complaint.priority] || ''}`;
                pBadge.textContent = complaint.priority.toUpperCase(); // SAFE
                tdPriority.appendChild(pBadge);
            } else {
                tdPriority.textContent = '-';
            }

            // Created
            const tdDate = document.createElement('td');
            tdDate.textContent = new Date(complaint.created_at).toLocaleDateString(); // SAFE

            // Action
            const tdAction = document.createElement('td');
            const link = document.createElement('a');
            link.href = `/complaint-detail.html?id=${complaint.id}`;
            link.className = 'link';
            link.textContent = 'View';
            tdAction.appendChild(link);

            tr.appendChild(tdId);
            tr.appendChild(tdSubject);
            tr.appendChild(tdUser);
            tr.appendChild(tdCat);
            tr.appendChild(tdStatus);
            tr.appendChild(tdPriority);
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
        loadComplaints(currentPage);
    });
    container.appendChild(prevBtn);

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.className = `page-btn${i === current ? ' active' : ''}`;
        btn.textContent = i;
        const pageNum = i;
        btn.addEventListener('click', () => {
            currentPage = pageNum;
            loadComplaints(currentPage);
        });
        container.appendChild(btn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = current === totalPages;
    nextBtn.addEventListener('click', () => {
        currentPage = current + 1;
        loadComplaints(currentPage);
    });
    container.appendChild(nextBtn);
}

// Debounced search to avoid firing on every keystroke
document.getElementById('searchInput').addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        loadComplaints(1);
    }, 400);
});

document.getElementById('statusFilter').addEventListener('change', () => {
    currentPage = 1;
    loadComplaints(1);
});

document.getElementById('priorityFilter').addEventListener('change', () => {
    currentPage = 1;
    loadComplaints(1);
});

document.getElementById('categoryFilter').addEventListener('change', () => {
    currentPage = 1;
    loadComplaints(1);
});

loadCategories();
loadComplaints(1);
