// tickets.js - Handles ticket management functionality

document.addEventListener('DOMContentLoaded', function() {
    // Load all tickets
    loadTickets();
    
    // Set up event listeners for filter buttons
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Load tickets with the selected filter
            const status = this.dataset.status;
            loadTickets(status);
        });
    });
    
    // Set up form submission for new ticket
    const newTicketForm = document.getElementById('new-ticket-form');
    if (newTicketForm) {
        newTicketForm.addEventListener('submit', createNewTicket);
    }
    
    // Set up event delegation for ticket list
    const ticketList = document.getElementById('ticket-list');
    if (ticketList) {
        ticketList.addEventListener('click', function(event) {
            // Check if a ticket row was clicked
            const ticketRow = event.target.closest('.ticket-row');
            if (ticketRow) {
                const ticketId = ticketRow.dataset.ticketId;
                loadTicketDetails(ticketId);
            }
        });
    }
});

// Load tickets based on status filter
function loadTickets(status = null) {
    // Show loading spinner
    const ticketList = document.getElementById('ticket-list');
    ticketList.innerHTML = `
        <tr>
            <td colspan="5" class="text-center py-4">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </td>
        </tr>
    `;
    
    // Build API URL with optional status filter
    let url = '/api/tickets';
    if (status && status !== 'all') {
        url += `?status=${status}`;
    }
    
    // Fetch tickets from API
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTickets(data.tickets);
            } else {
                showErrorAlert('Failed to load tickets: ' + data.message);
                ticketList.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-4">
                            <div class="alert alert-danger mb-0">Failed to load tickets</div>
                        </td>
                    </tr>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorAlert('An error occurred while loading tickets');
            ticketList.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        <div class="alert alert-danger mb-0">Error loading tickets</div>
                    </td>
                </tr>
            `;
        });
}

// Display tickets in the table
function displayTickets(tickets) {
    const ticketList = document.getElementById('ticket-list');
    
    if (tickets.length === 0) {
        ticketList.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="alert alert-info mb-0">No tickets found</div>
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort tickets by created date (newest first)
    tickets.sort((a, b) => {
        return new Date(b.created_at) - new Date(a.created_at);
    });
    
    // Generate HTML for each ticket
    const ticketHtml = tickets.map(ticket => {
        const createdDate = new Date(ticket.created_at).toLocaleString();
        
        return `
            <tr class="ticket-row" data-ticket-id="${ticket.ticket_id}">
                <td>
                    <span class="status-indicator status-${ticket.status.toLowerCase()}"></span>
                    ${ticket.ticket_id}
                </td>
                <td>${ticket.issue_category}</td>
                <td>
                    <span class="priority-indicator priority-${ticket.priority.toLowerCase()}">${ticket.priority}</span>
                </td>
                <td>${truncateText(ticket.description, 50)}</td>
                <td>${createdDate}</td>
            </tr>
        `;
    }).join('');
    
    ticketList.innerHTML = ticketHtml;
}

// Load details for a specific ticket
function loadTicketDetails(ticketId) {
    // Show loading spinner in modal
    const modalBody = document.querySelector('#ticket-detail-modal .modal-body');
    modalBody.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    // Show modal
    const ticketModal = new bootstrap.Modal(document.getElementById('ticket-detail-modal'));
    ticketModal.show();
    
    // Fetch ticket details from API
    fetch(`/api/tickets/${ticketId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTicketDetails(data.ticket, data.conversations);
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        Failed to load ticket details: ${data.message}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    An error occurred while loading ticket details
                </div>
            `;
        });
}

// Display ticket details in the modal
function displayTicketDetails(ticket, conversations) {
    const modalTitle = document.querySelector('#ticket-detail-modal .modal-title');
    const modalBody = document.querySelector('#ticket-detail-modal .modal-body');
    
    // Update modal title
    modalTitle.textContent = `Ticket: ${ticket.ticket_id}`;
    
    // Format created date
    const createdDate = new Date(ticket.created_at).toLocaleString();
    
    // Generate HTML for ticket details
    const ticketHtml = `
        <div class="ticket-details mb-4">
            <div class="row mb-3">
                <div class="col-md-6">
                    <p><strong>Category:</strong> ${ticket.issue_category}</p>
                    <p><strong>Priority:</strong> 
                        <span class="priority-indicator priority-${ticket.priority.toLowerCase()}">${ticket.priority}</span>
                    </p>
                    <p><strong>Status:</strong> 
                        <span class="badge bg-${getStatusColor(ticket.status)}">${ticket.status}</span>
                    </p>
                </div>
                <div class="col-md-6">
                    <p><strong>Created:</strong> ${createdDate}</p>
                    <p><strong>Sentiment:</strong> 
                        <span class="sentiment-indicator sentiment-${ticket.sentiment.toLowerCase()}">${ticket.sentiment}</span>
                    </p>
                    <p><strong>Resolution:</strong> ${ticket.resolution_status}</p>
                </div>
            </div>
            
            <div class="description-box p-3 mb-3 border rounded bg-dark">
                <h6>Description:</h6>
                <p>${ticket.description}</p>
            </div>
            
            ${ticket.resolution ? 
                `<div class="resolution-box p-3 mb-3 border rounded bg-dark">
                    <h6>Resolution:</h6>
                    <p>${ticket.resolution}</p>
                </div>` : ''
            }
        </div>
        
        <h5>Conversation History</h5>
        <div class="chat-container border rounded p-3 mb-3 bg-dark">
            ${conversations.length > 0 ? 
                conversations.map(conv => {
                    const timestamp = new Date(conv.timestamp).toLocaleTimeString();
                    return `
                        <div class="message ${conv.sender}-message">
                            <div class="message-content">${conv.message}</div>
                            <div class="message-timestamp small text-muted">${timestamp}</div>
                        </div>
                    `;
                }).join('') : 
                '<p class="text-center text-muted">No conversation history</p>'
            }
        </div>
        
        <div class="response-form">
            <h5>Add Response</h5>
            <div class="mb-3">
                <textarea class="form-control" id="response-text" rows="3" placeholder="Type your response..."></textarea>
            </div>
            
            <div class="d-flex justify-content-between">
                <button type="button" class="btn btn-primary" onclick="addResponse('${ticket.ticket_id}')">
                    Send Response
                </button>
                
                <button type="button" class="btn btn-info" onclick="getSuggestedSolutions('${ticket.ticket_id}')">
                    Get AI Suggestions
                </button>
                
                <div class="dropdown">
                    <button class="btn btn-secondary dropdown-toggle" type="button" id="statusDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                        Update Status
                    </button>
                    <ul class="dropdown-menu" aria-labelledby="statusDropdown">
                        <li><a class="dropdown-item" href="#" onclick="updateTicketStatus('${ticket.ticket_id}', 'Open')">Open</a></li>
                        <li><a class="dropdown-item" href="#" onclick="updateTicketStatus('${ticket.ticket_id}', 'Closed')">Closed</a></li>
                        <li><a class="dropdown-item" href="#" onclick="updateTicketStatus('${ticket.ticket_id}', 'Escalated')">Escalated</a></li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div id="suggestions-container" class="mt-3" style="display: none;"></div>
    `;
    
    modalBody.innerHTML = ticketHtml;
}

// Add a response to a ticket
function addResponse(ticketId) {
    const responseText = document.getElementById('response-text').value.trim();
    
    if (!responseText) {
        alert('Please enter a response');
        return;
    }
    
    // Disable input and button
    document.getElementById('response-text').disabled = true;
    const sendButton = document.querySelector('.response-form .btn-primary');
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
    
    // Send response to API
    fetch(`/api/tickets/${ticketId}/conversation`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: responseText,
            sender: 'agent'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add the response to the conversation
            const chatContainer = document.querySelector('.chat-container');
            const timestamp = new Date().toLocaleTimeString();
            
            const messageHtml = `
                <div class="message agent-message">
                    <div class="message-content">${responseText}</div>
                    <div class="message-timestamp small text-muted">${timestamp}</div>
                </div>
            `;
            
            chatContainer.innerHTML += messageHtml;
            
            // Clear and enable the textarea
            document.getElementById('response-text').value = '';
            document.getElementById('response-text').disabled = false;
            sendButton.disabled = false;
            sendButton.textContent = 'Send Response';
            
            // Scroll to bottom of chat
            chatContainer.scrollTop = chatContainer.scrollHeight;
        } else {
            alert('Failed to send response: ' + data.message);
            document.getElementById('response-text').disabled = false;
            sendButton.disabled = false;
            sendButton.textContent = 'Send Response';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while sending the response');
        document.getElementById('response-text').disabled = false;
        sendButton.disabled = false;
        sendButton.textContent = 'Send Response';
    });
}

// Get AI-suggested solutions for a ticket
function getSuggestedSolutions(ticketId) {
    // Show loading in suggestions container
    const suggestionsContainer = document.getElementById('suggestions-container');
    suggestionsContainer.style.display = 'block';
    suggestionsContainer.innerHTML = `
        <div class="card">
            <div class="card-header bg-info text-white">
                <i class="fas fa-robot me-2"></i> AI Suggested Solutions
            </div>
            <div class="card-body text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Getting AI suggestions...</p>
            </div>
        </div>
    `;
    
    // Fetch suggestions from API
    fetch(`/api/tickets/${ticketId}/suggest-solutions`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.solutions.length > 0) {
                // Display suggestions
                let solutionsHtml = `
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <i class="fas fa-robot me-2"></i> AI Suggested Solutions
                        </div>
                        <div class="card-body">
                            <div class="list-group">
                `;
                
                data.solutions.forEach((solution, index) => {
                    solutionsHtml += `
                        <a href="#" class="list-group-item list-group-item-action" onclick="useSolution('${ticketId}', ${index})">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1">Solution ${index + 1}</h6>
                                ${solution.success_rate ? 
                                    `<small class="text-success">${Math.round(solution.success_rate * 100)}% success rate</small>` : 
                                    `<small class="text-muted">New solution</small>`
                                }
                            </div>
                            <p class="mb-1">${truncateText(solution.solution_text, 150)}</p>
                        </a>
                    `;
                });
                
                solutionsHtml += `
                            </div>
                        </div>
                    </div>
                `;
                
                suggestionsContainer.innerHTML = solutionsHtml;
            } else {
                suggestionsContainer.innerHTML = `
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <i class="fas fa-robot me-2"></i> AI Suggested Solutions
                        </div>
                        <div class="card-body">
                            <p class="text-center">No suitable solutions found. Please provide a custom response.</p>
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            suggestionsContainer.innerHTML = `
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <i class="fas fa-robot me-2"></i> AI Suggested Solutions
                    </div>
                    <div class="card-body">
                        <div class="alert alert-danger">
                            Failed to get suggestions. Please try again.
                        </div>
                    </div>
                </div>
            `;
        });
}

// Use a suggested solution
function useSolution(ticketId, solutionIndex) {
    // Get the solution text
    const solutionElements = document.querySelectorAll('#suggestions-container .list-group-item');
    if (solutionIndex >= solutionElements.length) {
        alert('Invalid solution index');
        return;
    }
    
    const solutionText = solutionElements[solutionIndex].querySelector('p').textContent;
    
    // Set the solution text in the response textarea
    document.getElementById('response-text').value = solutionText;
    
    // Focus on the textarea
    document.getElementById('response-text').focus();
}

// Update ticket status
function updateTicketStatus(ticketId, status) {
    // Confirm status change
    if (!confirm(`Are you sure you want to mark this ticket as ${status}?`)) {
        return;
    }
    
    // Send update to API
    fetch(`/api/tickets/${ticketId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            status: status,
            resolution_status: status === 'Closed' ? 'Resolved' : 'Pending'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const statusBadge = document.querySelector('.ticket-details .badge');
            statusBadge.textContent = status;
            statusBadge.className = `badge bg-${getStatusColor(status)}`;
            
            // If closed, also update resolution status
            if (status === 'Closed') {
                const resolutionText = document.querySelector('.ticket-details p:contains("Resolution")');
                if (resolutionText) {
                    resolutionText.innerHTML = '<strong>Resolution:</strong> Resolved';
                }
            }
            
            // Show success message
            showSuccessAlert(`Ticket status updated to ${status}`);
            
            // Refresh ticket list in background
            loadTickets(null);
        } else {
            alert('Failed to update ticket status: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the ticket status');
    });
}

// Create a new ticket
function createNewTicket(event) {
    event.preventDefault();
    
    // Get form data
    const description = document.getElementById('new-ticket-description').value.trim();
    
    if (!description) {
        alert('Please enter a description');
        return;
    }
    
    // Disable form
    const submitButton = document.querySelector('#new-ticket-form button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
    
    // Create ticket via API
    fetch('/api/tickets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            description: description
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear form
            document.getElementById('new-ticket-description').value = '';
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('new-ticket-modal'));
            modal.hide();
            
            // Show success message
            showSuccessAlert('Ticket created successfully');
            
            // Reload tickets
            loadTickets(null);
        } else {
            alert('Failed to create ticket: ' + data.message);
        }
        
        // Re-enable form
        submitButton.disabled = false;
        submitButton.textContent = 'Create Ticket';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while creating the ticket');
        
        // Re-enable form
        submitButton.disabled = false;
        submitButton.textContent = 'Create Ticket';
    });
}

// Helper Functions

// Truncate text to specified length
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// Get Bootstrap color class for ticket status
function getStatusColor(status) {
    switch (status.toLowerCase()) {
        case 'open':
            return 'info';
        case 'closed':
            return 'success';
        case 'escalated':
            return 'danger';
        default:
            return 'secondary';
    }
}

// Show success alert
function showSuccessAlert(message) {
    const alertContainer = document.getElementById('alert-container');
    
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.role = 'alert';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                alertContainer.removeChild(alert);
            }, 150);
        }, 3000);
    }
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
