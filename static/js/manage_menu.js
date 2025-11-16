let editingId = null;

// Image URL preview
document.getElementById('imageUrl')?.addEventListener('input', function(e) {
    const url = e.target.value.trim();
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
        previewImg.src = url;
        preview.style.display = 'block';
        previewImg.onerror = function() {
            preview.style.display = 'none';
            showNotification('Invalid image URL', 'error');
        };
    } else {
        preview.style.display = 'none';
    }
});

function switchImageTab(tab) {
    const uploadTab = document.getElementById('uploadTab');
    const urlTab = document.getElementById('urlTab');
    const uploadBtn = document.querySelector('.tab-btn[onclick="switchImageTab(\'upload\')"]');
    const urlBtn = document.querySelector('.tab-btn[onclick="switchImageTab(\'url\')"]');
    
    if (tab === 'upload') {
        uploadTab.classList.add('active');
        urlTab.classList.remove('active');
        uploadBtn.classList.add('active');
        urlBtn.classList.remove('active');
        document.getElementById('imageUrl').value = '';
        document.getElementById('imagePreview').style.display = 'none';
    } else {
        urlTab.classList.add('active');
        uploadTab.classList.remove('active');
        urlBtn.classList.add('active');
        uploadBtn.classList.remove('active');
        document.getElementById('image').value = '';
    }
}

document.getElementById('menuForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const menuId = document.getElementById('menuId').value;
    
    // If using URL, remove file input from formData
    const imageUrl = document.getElementById('imageUrl').value.trim();
    if (imageUrl) {
        formData.append('image_url', imageUrl);
        formData.delete('image'); // Remove file if URL is provided
    }
    
    if (editingId) {
        // Update existing item
        fetch(`/api/menu/${editingId}`, {
            method: 'PUT',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Menu item updated successfully!');
                resetForm();
                location.reload(); // Reload to show updated data
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error updating menu item', 'error');
        });
    } else {
        // Create new item
        fetch('/api/menu', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Menu item added successfully!');
                resetForm();
                location.reload(); // Reload to show new item
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error adding menu item', 'error');
        });
    }
});

function editItem(id, name, price, description, imagePath) {
    editingId = id;
    document.getElementById('menuId').value = id;
    document.getElementById('name').value = name;
    document.getElementById('price').value = price;
    document.getElementById('description').value = description || '';
    document.getElementById('formTitle').textContent = 'Edit Menu Item';
    document.getElementById('submitBtn').textContent = 'Update Item';
    document.getElementById('cancelBtn').style.display = 'inline-block';
    
    // Handle image - if it's a URL, switch to URL tab
    if (imagePath && (imagePath.startsWith('http://') || imagePath.startsWith('https://'))) {
        switchImageTab('url');
        document.getElementById('imageUrl').value = imagePath;
        document.getElementById('previewImg').src = imagePath;
        document.getElementById('imagePreview').style.display = 'block';
    } else {
        switchImageTab('upload');
    }
    
    // Scroll to form
    document.querySelector('.menu-form-section').scrollIntoView({ behavior: 'smooth' });
}

function deleteItem(id) {
    if (confirm('Are you sure you want to delete this menu item?')) {
        fetch(`/api/menu/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Menu item deleted successfully!');
                location.reload(); // Reload to show updated list
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error deleting menu item', 'error');
        });
    }
}

function resetForm() {
    editingId = null;
    document.getElementById('menuForm').reset();
    document.getElementById('menuId').value = '';
    document.getElementById('formTitle').textContent = 'Add New Menu Item';
    document.getElementById('submitBtn').textContent = 'Add Item';
    document.getElementById('cancelBtn').style.display = 'none';
    switchImageTab('upload');
    document.getElementById('imagePreview').style.display = 'none';
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

