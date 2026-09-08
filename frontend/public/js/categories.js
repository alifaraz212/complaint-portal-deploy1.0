if (redirectIfNotAdmin()) throw new Error('Not admin');

// Track which row is being edited
let editingId = null;

async function loadCategories() {
    const tbody = document.getElementById('categoriesTable');
    tbody.innerHTML = '';

    try {
        // Admin sees all categories including inactive
        const categories = await apiRequest('/complaints/categories/');

        if (!categories.length) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 4;
            td.className = 'empty';
            td.textContent = 'No categories yet. Add one above.';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        categories.forEach(cat => renderCategoryRow(cat, tbody));

    } catch (error) {
        showError('Failed to load categories: ' + error.message);
    }
}

function renderCategoryRow(cat, tbody) {
    // Main row
    const tr = document.createElement('tr');
    tr.id = `row-${cat.id}`;

    // Name
    const tdName = document.createElement('td');
    tdName.textContent = cat.name; // SAFE

    // Description
    const tdDesc = document.createElement('td');
    tdDesc.textContent = cat.description || '-'; // SAFE

    // Status badge
    const tdStatus = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = `badge ${cat.is_active ? 'badge-active' : 'badge-inactive'}`;
    badge.textContent = cat.is_active ? 'Active' : 'Inactive'; // SAFE
    tdStatus.appendChild(badge);

    // Actions
    const tdActions = document.createElement('td');
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'actions';

    // Edit button
    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-warning btn-sm';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => toggleEditForm(cat));
    actionsDiv.appendChild(editBtn);

    // Deactivate/Activate button
    const toggleBtn = document.createElement('button');
    toggleBtn.className = `btn btn-sm ${cat.is_active ? 'btn-danger' : 'btn-primary'}`;
    toggleBtn.textContent = cat.is_active ? 'Deactivate' : 'Activate';
    toggleBtn.addEventListener('click', () => toggleCategory(cat));
    actionsDiv.appendChild(toggleBtn);

    tdActions.appendChild(actionsDiv);

    tr.appendChild(tdName);
    tr.appendChild(tdDesc);
    tr.appendChild(tdStatus);
    tr.appendChild(tdActions);
    tbody.appendChild(tr);

    // Edit form row (hidden by default)
    const editTr = document.createElement('tr');
    editTr.id = `edit-row-${cat.id}`;

    const editTd = document.createElement('td');
    editTd.colSpan = 4;

    const editForm = document.createElement('div');
    editForm.className = 'edit-form';
    editForm.id = `edit-form-${cat.id}`;

    // Edit name field
    const nameGroup = document.createElement('div');
    nameGroup.className = 'form-group';
    const nameLabel = document.createElement('label');
    nameLabel.textContent = 'Name';
    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.id = `edit-name-${cat.id}`;
    nameInput.value = cat.name; // Safe: value not innerHTML
    nameGroup.appendChild(nameLabel);
    nameGroup.appendChild(nameInput);

    // Edit description field
    const descGroup = document.createElement('div');
    descGroup.className = 'form-group';
    const descLabel = document.createElement('label');
    descLabel.textContent = 'Description';
    const descInput = document.createElement('textarea');
    descInput.id = `edit-desc-${cat.id}`;
    descInput.value = cat.description || ''; // Safe: value not innerHTML
    descGroup.appendChild(descLabel);
    descGroup.appendChild(descInput);

    // Save / Cancel buttons
    const footer = document.createElement('div');
    footer.className = 'form-footer';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-sm btn-danger';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.addEventListener('click', () => closeEditForm(cat.id));

    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-sm btn-primary';
    saveBtn.textContent = 'Save';
    saveBtn.addEventListener('click', () => saveCategory(cat.id));

    footer.appendChild(cancelBtn);
    footer.appendChild(saveBtn);

    editForm.appendChild(nameGroup);
    editForm.appendChild(descGroup);
    editForm.appendChild(footer);
    editTd.appendChild(editForm);
    editTr.appendChild(editTd);
    tbody.appendChild(editTr);
}

function toggleEditForm(cat) {
    // Close previously open edit form
    if (editingId && editingId !== cat.id) {
        closeEditForm(editingId);
    }
    const form = document.getElementById(`edit-form-${cat.id}`);
    if (form) {
        form.classList.toggle('visible');
        editingId = form.classList.contains('visible') ? cat.id : null;
    }
}

function closeEditForm(id) {
    const form = document.getElementById(`edit-form-${id}`);
    if (form) form.classList.remove('visible');
    if (editingId === id) editingId = null;
}

async function saveCategory(id) {
    const name = document.getElementById(`edit-name-${id}`).value.trim();
    const description = document.getElementById(`edit-desc-${id}`).value.trim();

    if (!name) {
        showError('Category name cannot be empty');
        return;
    }

    try {
        await apiRequest(`/complaints/categories/${id}/`, {
            method: 'PUT',
            body: JSON.stringify({ name, description })
        });
        showSuccess('Category updated');
        loadCategories();
    } catch (error) {
        showError(error.message);
    }
}

async function toggleCategory(cat) {
    const action = cat.is_active ? 'deactivate' : 'activate';
    if (!confirm(`Are you sure you want to ${action} "${cat.name}"?`)) return;

    try {
        if (cat.is_active) {
            // Deactivate = DELETE (soft deactivate)
            await apiRequest(`/complaints/categories/${cat.id}/`, {
                method: 'DELETE'
            });
        } else {
            // Activate = PUT with is_active: true
            await apiRequest(`/complaints/categories/${cat.id}/`, {
                method: 'PUT',
                body: JSON.stringify({ name: cat.name, description: cat.description || '', is_active: true })
            });
        }
        loadCategories();
    } catch (error) {
        showError(error.message);
    }
}

// Add new category form
document.getElementById('addCategoryForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('newName').value.trim();
    const description = document.getElementById('newDescription').value.trim();

    if (!name) {
        showError('Category name is required');
        return;
    }

    try {
        await apiRequest('/complaints/categories/create/', {
            method: 'POST',
            body: JSON.stringify({ name, description })
        });
        document.getElementById('newName').value = '';
        document.getElementById('newDescription').value = '';
        showSuccess('Category created');
        loadCategories();
    } catch (error) {
        showError(error.message);
    }
});

loadCategories();
