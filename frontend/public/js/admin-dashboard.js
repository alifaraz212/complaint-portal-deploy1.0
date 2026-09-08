if (redirectIfNotAdmin()) throw new Error('Not admin');

const statusColors = {
    'open': 'badge-open',
    'in_progress': 'badge-in_progress',
    'resolved': 'badge-resolved',
    'closed': 'badge-closed'
};

async function loadStats() {
    try {
        const stats = await apiRequest('/dashboard/stats/');

        // Top cards
        setTextSafe('totalComplaints', stats.total_complaints);
        setTextSafe('thisMonth', stats.this_month_count);
        setTextSafe('lastMonth', stats.last_month_count);
        setTextSafe('avgResolution', stats.average_resolution_time_hours.toFixed(2));

        // By status breakdown
        const byStatusEl = document.getElementById('byStatus');
        byStatusEl.innerHTML = '';
        Object.entries(stats.by_status).forEach(([key, val]) => {
            const row = document.createElement('div');
            row.className = 'breakdown-row';

            const k = document.createElement('span');
            k.className = 'breakdown-key';
            k.textContent = key.replace('_', ' '); // SAFE

            const v = document.createElement('span');
            v.className = 'breakdown-val';
            v.textContent = val; // SAFE

            row.appendChild(k);
            row.appendChild(v);
            byStatusEl.appendChild(row);
        });

        // By priority breakdown
        const byPriorityEl = document.getElementById('byPriority');
        byPriorityEl.innerHTML = '';
        Object.entries(stats.by_priority).forEach(([key, val]) => {
            const row = document.createElement('div');
            row.className = 'breakdown-row';

            const k = document.createElement('span');
            k.className = 'breakdown-key';
            k.textContent = key; // SAFE

            const v = document.createElement('span');
            v.className = 'breakdown-val';
            v.textContent = val; // SAFE

            row.appendChild(k);
            row.appendChild(v);
            byPriorityEl.appendChild(row);
        });

        // By category breakdown
        const byCategoryEl = document.getElementById('byCategory');
        byCategoryEl.innerHTML = '';
        Object.entries(stats.by_category).forEach(([key, val]) => {
            const row = document.createElement('div');
            row.className = 'breakdown-row';

            const k = document.createElement('span');
            k.className = 'breakdown-key';
            k.textContent = key; // SAFE

            const v = document.createElement('span');
            v.className = 'breakdown-val';
            v.textContent = val; // SAFE

            row.appendChild(k);
            row.appendChild(v);
            byCategoryEl.appendChild(row);
        });

    } catch (error) {
        showError('Failed to load stats: ' + error.message);
    }
}

async function loadRecentActivity() {
    try {
        const data = await apiRequest('/dashboard/recent/');

        // Recent complaints table
        const tbody = document.getElementById('recentComplaints');
        tbody.innerHTML = '';
        (data.recent_complaints || []).forEach(c => {
            const tr = document.createElement('tr');

            const tdId = document.createElement('td');
            const link = document.createElement('a');
            link.href = `/complaint-detail.html?id=${c.id}`;
            link.className = 'link';
            link.textContent = c.complaint_number; // SAFE
            tdId.appendChild(link);

            const tdSubject = document.createElement('td');
            tdSubject.textContent = c.subject; // SAFE

            const tdStatus = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = `badge ${statusColors[c.status] || ''}`;
            badge.textContent = c.status.replace('_', ' ').toUpperCase(); // SAFE
            tdStatus.appendChild(badge);

            tr.appendChild(tdId);
            tr.appendChild(tdSubject);
            tr.appendChild(tdStatus);
            tbody.appendChild(tr);
        });

        // Recent status changes
        const activityEl = document.getElementById('recentActivity');
        activityEl.innerHTML = '';

        // Build a map of complaint id → complaint_number from recent_complaints
        const complaintMap = {};
        (data.recent_complaints || []).forEach(c => {
            complaintMap[c.id] = c.complaint_number;
        });

        (data.recent_status_changes || []).forEach(log => {
            const div = document.createElement('div');
            div.className = 'breakdown-row';
            div.style.flexDirection = 'column';
            div.style.alignItems = 'flex-start';
            div.style.gap = '2px';

            const top = document.createElement('span');
            top.className = 'breakdown-key';
            // complaint_number now comes directly from ActivityLogSerializer
            const compLabel = log.complaint_number || `Complaint ID ${log.complaint}`;
            top.textContent = `${compLabel}: ${log.old_value} → ${log.new_value}`; // SAFE

            const bottom = document.createElement('span');
            bottom.style.cssText = 'font-size: 11px; color: #aaa;';
            bottom.textContent = `by ${log.performed_by_email} at ${new Date(log.timestamp).toLocaleString()}`; // SAFE

            div.appendChild(top);
            div.appendChild(bottom);
            activityEl.appendChild(div);
        });

    } catch (error) {
        showError('Failed to load recent activity: ' + error.message);
    }
}

loadStats();
loadRecentActivity();
