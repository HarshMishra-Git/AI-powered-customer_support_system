// dashboard.js - Handles dashboard functionality and visualizations

document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard statistics
    loadDashboardStats();
    
    // Set up refresh button
    const refreshButton = document.getElementById('refresh-dashboard');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadDashboardStats);
    }
    
    // Set up auto-refresh (every 60 seconds) only if we're on the dashboard page
    const dashboardContainer = document.querySelector('.dashboard-card');
    if (dashboardContainer) {
        setInterval(loadDashboardStats, 60000);
    }
});

// Helper function to safely update element text content
function safeSetText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

// Load dashboard statistics from the API
function loadDashboardStats() {
    // Show loading indicators
    document.querySelectorAll('.stats-loading').forEach(el => {
        el.style.display = 'block';
    });
    
    // Hide chart elements while loading
    document.querySelectorAll('.chart-container').forEach(el => {
        el.style.display = 'none';
    });
    
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTicketStats(data.ticket_counts);
                updateCategoryChart(data.category_counts);
                updateResolutionTimeStats(data.avg_resolution_time);
                updateSuccessRateChart(data.solution_success_rates);
                
                // Hide loading indicators
                document.querySelectorAll('.stats-loading').forEach(el => {
                    el.style.display = 'none';
                });
                
                // Show chart elements
                document.querySelectorAll('.chart-container').forEach(el => {
                    el.style.display = 'block';
                });
                
                // Update last refreshed time
                document.getElementById('last-refreshed').textContent = new Date().toLocaleTimeString();
            } else {
                console.error('Error loading dashboard stats:', data.message);
                showErrorAlert('Failed to load dashboard statistics');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorAlert('Failed to load dashboard statistics');
            
            // Hide loading indicators
            document.querySelectorAll('.stats-loading').forEach(el => {
                el.style.display = 'none';
            });
        });
}

// Update ticket count statistics
function updateTicketStats(counts) {
    safeSetText('open-tickets', counts.open);
    safeSetText('closed-tickets', counts.closed);
    safeSetText('escalated-tickets', counts.escalated);
    safeSetText('total-tickets', counts.total);
    
    // Update chart for ticket status distribution
    const statusCtx = document.getElementById('ticket-status-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.ticketStatusChart) {
        window.ticketStatusChart.destroy();
    }
    
    window.ticketStatusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['Open', 'Closed', 'Escalated'],
            datasets: [{
                data: [counts.open, counts.closed, counts.escalated],
                backgroundColor: [
                    '#0dcaf0', // info
                    '#198754', // success
                    '#dc3545'  // danger
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'white'
                    }
                }
            }
        }
    });
}

// Update category distribution chart
function updateCategoryChart(categoryCounts) {
    const categories = Object.keys(categoryCounts);
    const counts = Object.values(categoryCounts);
    
    const categoryCtx = document.getElementById('category-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.categoryChart) {
        window.categoryChart.destroy();
    }
    
    window.categoryChart = new Chart(categoryCtx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Ticket Count',
                data: counts,
                backgroundColor: '#6f42c1', // purple
                borderColor: '#6610f2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: 'white',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                }
            }
        }
    });
}

// Update average resolution time statistics
function updateResolutionTimeStats(avgTime) {
    // Ensure resolution time is positive and handle null/undefined
    const resolvedTime = avgTime ? Math.abs(avgTime) : 0;
    const element = document.getElementById('avg-resolution-time');
    if (element) {
        element.textContent = resolvedTime.toFixed(2) + ' hours';
    }
    
    // Hide loading and show value
    const loadingElements = document.querySelectorAll('.stats-loading');
    const valueElements = document.querySelectorAll('.stats-value');
    
    loadingElements.forEach(el => el.style.display = 'none');
    valueElements.forEach(el => el.style.display = 'block');
}

// Update solution success rate chart
function updateSuccessRateChart(successRates) {
    // Check if successRates is an array of objects (from API) or direct object mapping
    let categories = [];
    let rates = [];
    
    if (Array.isArray(successRates)) {
        // API returns an array of objects with category, solution, success_rate, usage_count
        for (const item of successRates) {
            categories.push(item.category);
            // Ensure the success rate is properly formatted (0-100 scale)
            const rate = item.success_rate > 1 ? item.success_rate : item.success_rate * 100;
            rates.push(Math.min(rate, 100)); // Cap at 100%
        }
    } else {
        // Object mapping of category -> success rate
        categories = Object.keys(successRates);
        rates = Object.values(successRates).map(rate => {
            // Ensure the success rate is properly formatted (0-100 scale)
            const formattedRate = rate > 1 ? rate : rate * 100;
            return Math.min(formattedRate, 100); // Cap at 100%
        });
    }
    
    // Handle case of empty data
    if (categories.length === 0) {
        // Add dummy data if no success rates available
        categories = ['No Data Available'];
        rates = [0];
    }
    
    const successCtx = document.getElementById('success-rate-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.successRateChart) {
        window.successRateChart.destroy();
    }
    
    // Format radar chart data
    window.successRateChart = new Chart(successCtx, {
        type: 'radar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Success Rate (%)',
                data: rates,
                backgroundColor: 'rgba(255, 193, 7, 0.2)', // warning
                borderColor: '#ffc107',
                borderWidth: 2,
                pointBackgroundColor: '#ffc107',
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: 'white'
                    },
                    ticks: {
                        backdropColor: 'rgba(0, 0, 0, 0)',
                        color: 'white',
                        // Ensure the scale starts from 0 and ends at 100 for percentages
                        min: 0,
                        max: 100,
                        stepSize: 20
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Show error alert
function showErrorAlert(message) {
    const alertContainer = document.getElementById('alert-container');
    
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.role = 'alert';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                alertContainer.removeChild(alert);
            }, 150);
        }, 5000);
    }
}
