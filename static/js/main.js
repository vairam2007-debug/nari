let cart = [];
let currentOrder = null;

// Load cart from session on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCart();
});

function addToCart(menuId, name, price) {
    fetch('/api/add-to-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            menu_id: menuId,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
            showNotification('Item added to cart!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding item to cart', 'error');
    });
}

function updateCartItem(menuId, quantity) {
    fetch('/api/update-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            menu_id: menuId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating cart', 'error');
    });
}

function removeFromCart(menuId) {
    fetch('/api/remove-from-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            menu_id: menuId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
            showNotification('Item removed from cart');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error removing item', 'error');
    });
}

function clearCart() {
    if (confirm('Are you sure you want to clear the cart?')) {
        fetch('/api/clear-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cart = [];
                updateCartDisplay();
                showNotification('Cart cleared');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error clearing cart', 'error');
        });
    }
}

function loadCart() {
    fetch('/api/get-cart', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateCartDisplay() {
    const cartItems = document.getElementById('cartItems');
    const cartSummary = document.getElementById('cartSummary');
    const cartTotal = document.getElementById('cartTotal');
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="empty-cart">Your cart is empty</p>';
        cartSummary.style.display = 'none';
        return;
    }
    
    cartSummary.style.display = 'block';
    
    let html = '';
    let total = 0;
    
    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        
        html += `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <p>₹${item.price.toFixed(2)} × ${item.quantity}</p>
                </div>
                <div class="cart-item-actions">
                    <button onclick="updateCartItem(${item.menu_id}, ${item.quantity - 1})" ${item.quantity <= 1 ? 'disabled' : ''}>-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateCartItem(${item.menu_id}, ${item.quantity + 1})">+</button>
                    <button class="remove-btn" onclick="removeFromCart(${item.menu_id})">×</button>
                </div>
                <div class="cart-item-total">
                    ₹${itemTotal.toFixed(2)}
                </div>
            </div>
        `;
    });
    
    cartItems.innerHTML = html;
    cartTotal.textContent = total.toFixed(2);
}

function checkout() {
    if (cart.length === 0) {
        showNotification('Cart is empty', 'error');
        return;
    }
    
    fetch('/api/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentOrder = data.order;
            showBill(data.order);
            cart = [];
            updateCartDisplay();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error during checkout', 'error');
    });
}

function showBill(order) {
    const modal = document.getElementById('billModal');
    const billContent = document.getElementById('billContent');
    
    let itemsHtml = '';
    order.items.forEach(item => {
        itemsHtml += `
            <tr>
                <td>${item.menu_name}</td>
                <td>${item.quantity}</td>
                <td>₹${item.price.toFixed(2)}</td>
                <td>₹${item.subtotal.toFixed(2)}</td>
            </tr>
        `;
    });
    
    billContent.innerHTML = `
        <div class="bill-header">
            <h2>Restaurant Bill</h2>
            <p>Order Number: <strong>${order.order_number}</strong></p>
            <p>Date: ${new Date(order.order_date).toLocaleString()}</p>
        </div>
        <table class="bill-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                ${itemsHtml}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3"><strong>Total Amount:</strong></td>
                    <td><strong>₹${order.total_amount.toFixed(2)}</strong></td>
                </tr>
            </tfoot>
        </table>
    `;
    
    modal.style.display = 'block';
}

function closeBillModal() {
    document.getElementById('billModal').style.display = 'none';
}

function printBill() {
    const printContent = document.getElementById('billContent').innerHTML;
    const originalContent = document.body.innerHTML;
    
    document.body.innerHTML = `
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            ${printContent}
        </div>
    `;
    
    window.print();
    
    document.body.innerHTML = originalContent;
    updateCartDisplay();
}

function generateQR() {
    if (!currentOrder) {
        showNotification('No order found', 'error');
        return;
    }
    
    const qrModal = document.getElementById('qrModal');
    const qrOrderNumber = document.getElementById('qrOrderNumber');
    const qrAmount = document.getElementById('qrAmount');
    
    // Display order information with static QR code
    qrOrderNumber.textContent = currentOrder.order_number;
    qrAmount.textContent = currentOrder.total_amount.toFixed(2);
    
    qrModal.style.display = 'block';
}

function closeQRModal() {
    document.getElementById('qrModal').style.display = 'none';
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

// Close modals when clicking outside
window.onclick = function(event) {
    const billModal = document.getElementById('billModal');
    const qrModal = document.getElementById('qrModal');
    
    if (event.target === billModal) {
        closeBillModal();
    }
    if (event.target === qrModal) {
        closeQRModal();
    }
}

