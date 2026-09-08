if (redirectIfNotAuthenticated()) throw new Error('Not authenticated');

const params = new URLSearchParams(window.location.search);
const complaintId = params.get('id');
const role = getUserRole();

if (!complaintId) {
    alert('No complaint ID provided');
    window.location.href = role === 'admin' ? '/admin-complaints.html' : '/user-dashboard.html';
}

// Set back link based on role
const backLink = document.getElementById('backLink');
if (role === 'admin') {
    backLink.href = '/admin-complaints.html';
    backLink.textContent = '← Back to All Complaints';
} else {
    backLink.href = '/user-dashboard.html';
    backLink.textContent = '← Back to My Complaints';
}

// Show admin sections if admin
if (role === 'admin') {
    document.querySelectorAll('.admin-section').forEach(el => {
        el.style.display = 'block';
    });
}

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

async function loadComplaint() {
    try {
        const complaint = await apiRequest(`/complaints/complaints/${complaintId}/`);
        renderComplaint(complaint);
        renderResponses(complaint.responses || []);

        if (role === 'admin') {
            renderActivityLog(complaint.activity_logs || []);
            // Pre-fill admin controls with current values
            if (complaint.status) document.getElementById('statusSelect').value = complaint.status;
            if (complaint.priority) document.getElementById('prioritySelect').value = complaint.priority;
            if (complaint.admin_notes) document.getElementById('adminNotes').value = complaint.admin_notes;
        }
    } catch (error) {
        showError(error.message);
    }
}

function renderComplaint(complaint) {
    const card = document.getElementById('complaintCard');
    card.innerHTML = ''; // Safe to clear since we build with createElement

    // Title
    const title = document.createElement('h3');
    title.textContent = complaint.complaint_number + ' — ' + complaint.subject;
    card.appendChild(title);

    // Meta grid
    const grid = document.createElement('div');
    grid.className = 'meta-grid';
    grid.style.marginTop = '16px';

    const fields = [
        { label: 'Status', value: complaint.status, badge: statusColors[complaint.status] },
        { label: 'Priority', value: complaint.priority || 'Not set', badge: complaint.priority ? priorityColors[complaint.priority] : null },
        { label: 'Category', value: complaint.category_name || '-' },
        { label: 'Submitted by', value: complaint.user_email || '-' },
        { label: 'Created', value: new Date(complaint.created_at).toLocaleString() },
        { label: 'Last Updated', value: new Date(complaint.updated_at).toLocaleString() },
    ];

    if (complaint.resolved_at) {
        fields.push({ label: 'Resolved At', value: new Date(complaint.resolved_at).toLocaleString() });
    }

    fields.forEach(field => {
        const item = document.createElement('div');
        item.className = 'meta-item';

        const lbl = document.createElement('label');
        lbl.textContent = field.label;

        const val = document.createElement('span');
        if (field.badge) {
            val.className = `badge ${field.badge}`;
        }
        val.textContent = field.value ? field.value.replace('_', ' ').toUpperCase() : '-';

        item.appendChild(lbl);
        item.appendChild(val);
        grid.appendChild(item);
    });

    card.appendChild(grid);

    // Description
    const descLabel = document.createElement('p');
    descLabel.style.cssText = 'margin-top: 20px; margin-bottom: 8px; font-size: 12px; color: #999; text-transform: uppercase; font-weight: 600;';
    descLabel.textContent = 'Description';

    const desc = document.createElement('p');
    desc.className = 'description-text';
    desc.textContent = complaint.description; // SAFE: textContent
    card.appendChild(descLabel);
    card.appendChild(desc);

    // Attachments
    if (complaint.attachments && complaint.attachments.length > 0) {
        const attLabel = document.createElement('p');
        attLabel.style.cssText = 'margin-top: 16px; margin-bottom: 8px; font-size: 12px; color: #999; text-transform: uppercase; font-weight: 600;';
        attLabel.textContent = 'Attachments';
        card.appendChild(attLabel);

        complaint.attachments.forEach(att => {
            const link = document.createElement('a');
            link.href = att.file_url || '#';
            link.target = '_blank';
            link.className = 'attachment-link';
            link.textContent = 'View Attachment ' + att.id;
            link.style.display = 'block';
            card.appendChild(link);
        });
    }
}

function renderResponses(responses) {
    const list = document.getElementById('responsesList');
    list.innerHTML = '';

    if (!responses.length) {
        const p = document.createElement('p');
        p.className = 'no-responses';
        p.textContent = 'No responses yet.';
        list.appendChild(p);
        return;
    }

    responses.forEach(resp => {
        const div = document.createElement('div');
        const isAdmin = resp.author_role === 'admin';
        div.className = `response ${isAdmin ? 'response-admin' : 'response-user'}`;

        const meta = document.createElement('p');
        meta.className = 'response-meta';
        const date = new Date(resp.created_at).toLocaleString();
        meta.textContent = `${resp.author_email} (${resp.author_role}) — ${date}`; // SAFE: textContent

        const msg = document.createElement('p');
        msg.className = 'response-message';
        msg.textContent = resp.message; // SAFE: textContent

        div.appendChild(meta);
        div.appendChild(msg);
        list.appendChild(div);
    });
}

function renderActivityLog(logs) {
    const list = document.getElementById('activityList');
    list.innerHTML = '';

    if (!logs.length) {
        const p = document.createElement('p');
        p.className = 'no-responses';
        p.textContent = 'No activity yet.';
        list.appendChild(p);
        return;
    }

    logs.forEach(log => {
        const div = document.createElement('div');
        div.className = 'activity-item';

        const action = document.createElement('span');
        action.className = 'activity-action';
        action.textContent = log.action.replace('_', ' ').toUpperCase(); // SAFE: textContent

        const detail = document.createElement('span');
        const oldVal = log.old_value || '—';
        const newVal = log.new_value || '—';
        const date = new Date(log.timestamp).toLocaleString();
        detail.textContent = ` — ${oldVal} → ${newVal} by ${log.performed_by_email} at ${date}`; // SAFE

        div.appendChild(action);
        div.appendChild(detail);
        list.appendChild(div);
    });
}

async function updateComplaint() {
    const status = document.getElementById('statusSelect').value;
    const priority = document.getElementById('prioritySelect').value;
    const admin_notes = document.getElementById('adminNotes').value.trim();

    const payload = {};
    if (status) payload.status = status;
    if (priority) payload.priority = priority;
    if (admin_notes !== '') payload.admin_notes = admin_notes;

    if (!Object.keys(payload).length) {
        showError('No changes to save');
        return;
    }

    try {
        await apiRequest(`/complaints/complaints/${complaintId}/update/`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
        showSuccess('Complaint updated successfully');
        loadComplaint(); // Reload to reflect changes — this also re-fills the fields with latest values
    } catch (error) {
        showError(error.message);
    }
}

async function submitReply() {
    const message = document.getElementById('replyMessage').value.trim();

    if (!message) {
        showError('Reply message cannot be empty');
        return;
    }

    try {
        await apiRequest(`/complaints/complaints/${complaintId}/responses/`, {
            method: 'POST',
            body: JSON.stringify({ message })
        });
        document.getElementById('replyMessage').value = '';
        loadComplaint(); // Reload to show new response
    } catch (error) {
        showError(error.message);
    }
}

loadComplaint();
