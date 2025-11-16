let dailySalesChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // Set current month and year
    const now = new Date();
    document.getElementById('month').value = now.getMonth() + 1;
    document.getElementById('year').value = now.getFullYear();
    
    // Load initial data
    loadSalesData();
});

function loadSalesData() {
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;
    
    fetch(`/api/sales-data?month=${month}&year=${year}`)
        .then(response => response.json())
        .then(data => {
            updateSummary(data);
            updateTopItems(data.top_items);
            updateDailyBreakdown(data.daily_sales);
            updateChart(data.daily_sales);
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error loading sales data', 'error');
        });
}

function updateSummary(data) {
    document.getElementById('totalSales').textContent = data.total_sales.toFixed(2);
    document.getElementById('totalOrders').textContent = data.total_orders;
    
    const avgOrderValue = data.total_orders > 0 ? (data.total_sales / data.total_orders) : 0;
    document.getElementById('avgOrderValue').textContent = avgOrderValue.toFixed(2);
}

function updateTopItems(items) {
    const tableBody = document.getElementById('topItemsTable');
    
    if (items.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3">No data available</td></tr>';
        return;
    }
    
    let html = '';
    items.forEach(item => {
        html += `
            <tr>
                <td>${item.name}</td>
                <td>${item.quantity}</td>
                <td>₹${item.revenue.toFixed(2)}</td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

function updateDailyBreakdown(dailySales) {
    const tableBody = document.getElementById('dailyBreakdownTable');
    
    if (dailySales.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3">No data available</td></tr>';
        return;
    }
    
    let html = '';
    dailySales.forEach(day => {
        html += `
            <tr>
                <td>${day.date}</td>
                <td>${day.orders}</td>
                <td>₹${day.total.toFixed(2)}</td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

function updateChart(dailySales) {
    const ctx = document.getElementById('dailySalesChart').getContext('2d');
    
    if (dailySalesChart) {
        dailySalesChart.destroy();
    }
    
    const labels = dailySales.map(day => day.date);
    const data = dailySales.map(day => day.total);
    
    dailySalesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Sales (₹)',
                data: data,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
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

