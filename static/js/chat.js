// chat.js - Handles the chat interface functionality

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatContainer = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatForm = document.getElementById('chat-form');
    const createTicketBtn = document.getElementById('create-ticket-btn');
    const chatHistory = [];
    
    // Create a unique session ID for this chat session
    const sessionId = 'chat_' + Math.random().toString(36).substring(2, 15);
    
    // Initialize the chat interface
    function initChat() {
        // Show loading while waiting for the initial greeting
        const loadingMessage = document.createElement('div');
        loadingMessage.id = 'loading-message';
        loadingMessage.className = 'message agent-message';
        loadingMessage.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Loading...';
        chatContainer.appendChild(loadingMessage);
        
        // Let the server initiate the conversation to ensure proper state management
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: 'Hello',
                conversation_history: [],
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) loadingMessage.remove();
            
            if (data.success) {
                // Add agent welcome message and category options
                addMessage(data.response, 'agent');
            } else {
                addMessage('Hello! I\'m your AI support assistant. How can I help you today?', 'agent');
            }
        })
        .catch(error => {
            // Remove loading indicator
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) loadingMessage.remove();
            
            console.error('Error initializing chat:', error);
            addMessage('Hello! I\'m your AI support assistant. How can I help you today?', 'agent');
        });
        
        // Focus on the input field
        messageInput.focus();
    }
    
    // Handle sending a message
    function sendMessage(e) {
        if (e) e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to the chat
        addMessage(message, 'user');
        
        // Clear the input field
        messageInput.value = '';
        
        // Show loading indicator
        const loadingMessage = document.createElement('div');
        loadingMessage.id = 'loading-message';
        loadingMessage.className = 'message agent-message';
        loadingMessage.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Thinking...';
        chatContainer.appendChild(loadingMessage);
        scrollToBottom();
        
        // Send message to the API with session ID for conversation state tracking
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_history: chatHistory,
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) loadingMessage.remove();
            
            if (data.success) {
                // Add agent response to chat
                addMessage(data.response, 'agent');
                
                // If a ticket was created through the conversation flow
                if (data.create_ticket && data.ticket_id) {
                    // Get the ticket details to display
                    fetch(`/api/tickets/${data.ticket_id}`)
                        .then(response => response.json())
                        .then(ticketData => {
                            if (ticketData.success) {
                                addTicketCreationMessage(ticketData.ticket);
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching ticket:', error);
                        });
                }
                // If a ticket was created immediately (legacy method)
                else if (data.create_ticket && data.ticket) {
                    addTicketCreationMessage(data.ticket);
                }
            } else {
                addMessage('Sorry, I encountered an error processing your request.', 'agent');
            }
        })
        .catch(error => {
            // Remove loading indicator
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) loadingMessage.remove();
            
            console.error('Error:', error);
            addMessage('Sorry, I experienced a technical issue. Please try again.', 'agent');
        });
    }
    
    // Add a message to the chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Check if we need to convert line breaks to HTML or preserve formatting
        if (sender === 'agent') {
            // Format numbered lists properly
            const formattedText = formatMessageText(text);
            messageDiv.innerHTML = formattedText;
        } else {
            // For user messages, just use text content
            messageDiv.textContent = text;
        }
        
        chatContainer.appendChild(messageDiv);
        
        // Add to chat history
        chatHistory.push({
            message: text,
            sender: sender
        });
        
        // Scroll to the bottom
        scrollToBottom();
    }
    
    // Format message text with proper HTML for lists, categories, etc.
    function formatMessageText(text) {
        // Store original text for sentiment analysis
        const originalText = text;
        
        // Replace numbered lists (e.g., "1. Step one\n2. Step two") with proper HTML
        let formattedText = text.replace(/(\d+\.\s[^\n]+)(\n|$)/g, '<li>$1</li>');
        
        // If we found list items, wrap them in a proper list
        if (formattedText.includes('<li>')) {
            formattedText = '<ol>' + formattedText + '</ol>';
        }
        
        // Replace category options with clickable elements
        if (formattedText.includes('select the category') || formattedText.includes('choose one of the following')) {
            // We'll capture all the category options and replace them with proper buttons
            const categoryRegex = /(\d+\.\s)([\w\s]+(?:Issue|Error|Bug|Failure|Support))(?=\n|<br>|$)/g;
            let match;
            let categoryOptions = [];
            
            // Find all category options in the text
            while ((match = categoryRegex.exec(formattedText)) !== null) {
                categoryOptions.push({
                    fullText: match[0],
                    numberPart: match[1],
                    categoryName: match[2]
                });
            }
            
            // Now replace each category option with a button
            categoryOptions.forEach(option => {
                const buttonId = `category-${Math.random().toString(36).substring(2, 10)}`;
                const buttonHtml = `<div id="${buttonId}" class="category-option">${option.numberPart}${option.categoryName}</div>`;
                
                // Replace the text with our button
                formattedText = formattedText.replace(option.fullText, buttonHtml);
                
                // Add event listener after DOM update
                setTimeout(() => {
                    const button = document.getElementById(buttonId);
                    if (button) {
                        button.addEventListener('click', function() {
                            sendCustomMessage(`${option.numberPart}${option.categoryName}`);
                        });
                    }
                }, 100);
            });
        }
        
        // Add styling for Yes/No responses for issue resolution
        if (formattedText.includes('Did these steps resolve your issue?')) {
            const yesButtonId = `yes-resolve-${Math.random().toString(36).substring(2, 10)}`;
            const noButtonId = `no-resolve-${Math.random().toString(36).substring(2, 10)}`;
            
            formattedText = formattedText.replace(/(Did these steps resolve your issue\?[\s\S]*?)(<br>|$)/, 
                '$1<div class="response-buttons mt-2">' +
                `<button id="${yesButtonId}" class="btn btn-sm btn-success me-2">Yes, resolved</button>` +
                `<button id="${noButtonId}" class="btn btn-sm btn-danger">No, still having issues</button>` +
                '</div>');
                
            // Add event listeners after the DOM is updated
            setTimeout(() => {
                const yesButton = document.getElementById(yesButtonId);
                const noButton = document.getElementById(noButtonId);
                
                if (yesButton) {
                    yesButton.addEventListener('click', function() {
                        sendCustomMessage('Yes, it\'s resolved');
                    });
                }
                
                if (noButton) {
                    noButton.addEventListener('click', function() {
                        sendCustomMessage('No, still having issues');
                    });
                }
            }, 100);
        }
        
        // Add "Yes/No" buttons for "anything else" questions
        if (formattedText.includes('Is there anything else you need assistance with today?') || 
            formattedText.includes('Is there anything else I can help you with?')) {
            const yesButtonId = `yes-more-${Math.random().toString(36).substring(2, 10)}`;
            const noButtonId = `no-more-${Math.random().toString(36).substring(2, 10)}`;
            
            formattedText = formattedText.replace(/(Is there anything else (?:you need assistance with today|I can help you with)\?[\s\S]*?)(<br>|$)/, 
                '$1<div class="response-buttons mt-2">' +
                `<button id="${yesButtonId}" class="btn btn-sm btn-primary me-2">Yes, I have another question</button>` +
                `<button id="${noButtonId}" class="btn btn-sm btn-secondary">No, that's all</button>` +
                '</div>');
                
            // Add event listeners after the DOM is updated
            setTimeout(() => {
                const yesButton = document.getElementById(yesButtonId);
                const noButton = document.getElementById(noButtonId);
                
                if (yesButton) {
                    yesButton.addEventListener('click', function() {
                        sendCustomMessage('Yes, I have another question');
                    });
                }
                
                if (noButton) {
                    noButton.addEventListener('click', function() {
                        sendCustomMessage('No, that\'s all for now. Thank you!');
                    });
                }
            }, 100);
        }
        
        // Add rating buttons when asked for feedback
        if (formattedText.includes('rate your experience')) {
            const starIds = [
                `star1-${Math.random().toString(36).substring(2, 10)}`,
                `star2-${Math.random().toString(36).substring(2, 10)}`,
                `star3-${Math.random().toString(36).substring(2, 10)}`,
                `star4-${Math.random().toString(36).substring(2, 10)}`,
                `star5-${Math.random().toString(36).substring(2, 10)}`
            ];
            
            formattedText = formattedText.replace(/(rate your experience[\s\S]*?)(<br>|$)/, 
                '$1<div class="star-rating mt-2">' +
                `<span id="${starIds[0]}" class="star me-1">⭐</span>` +
                `<span id="${starIds[1]}" class="star me-1">⭐</span>` +
                `<span id="${starIds[2]}" class="star me-1">⭐</span>` +
                `<span id="${starIds[3]}" class="star me-1">⭐</span>` +
                `<span id="${starIds[4]}" class="star">⭐</span>` +
                '</div>');
                
            // Add event listeners after the DOM is updated
            setTimeout(() => {
                for (let i = 0; i < starIds.length; i++) {
                    const starButton = document.getElementById(starIds[i]);
                    if (starButton) {
                        starButton.addEventListener('click', function() {
                            sendCustomMessage(`${i+1} star${i > 0 ? 's' : ''}`);
                        });
                    }
                }
            }, 100);
        }
        
        // Add quick action buttons for common support scenarios
        if (formattedText.includes('I can help with that') || formattedText.includes('I understand your issue')) {
            // Create unique IDs for each button
            const moreInfoId = `more-info-${Math.random().toString(36).substring(2, 10)}`;
            const commonSolutionsId = `common-solutions-${Math.random().toString(36).substring(2, 10)}`;
            const createTicketId = `create-ticket-${Math.random().toString(36).substring(2, 10)}`;
            
            formattedText += '<div class="quick-actions mt-3">' +
                `<button id="${moreInfoId}" class="btn btn-sm btn-outline-primary me-2">More Info</button>` +
                `<button id="${commonSolutionsId}" class="btn btn-sm btn-outline-info me-2">Common Solutions</button>` +
                `<button id="${createTicketId}" class="btn btn-sm btn-outline-warning">Create Ticket</button>` +
                '</div>';
                
            // Add event listeners after the DOM is updated
            setTimeout(() => {
                const moreInfoBtn = document.getElementById(moreInfoId);
                const commonSolutionsBtn = document.getElementById(commonSolutionsId);
                const createTicketBtn = document.getElementById(createTicketId);
                
                if (moreInfoBtn) {
                    moreInfoBtn.addEventListener('click', function() {
                        sendCustomMessage('Tell me more about this issue');
                    });
                }
                
                if (commonSolutionsBtn) {
                    commonSolutionsBtn.addEventListener('click', function() {
                        sendCustomMessage('What are common solutions?');
                    });
                }
                
                if (createTicketBtn) {
                    createTicketBtn.addEventListener('click', function() {
                        sendCustomMessage('Create a support ticket');
                    });
                }
            }, 100);
        }
        
        // Add contextual emoji suggestions
        if (!formattedText.includes('emoji-suggestions') && originalText.length > 10) {
            // In a real implementation, we would call the sentiment analyzer API here
            // For now, we'll use a simpler approach with predefined emojis
            const emojiSuggestions = getEmojiSuggestions(originalText);
            if (emojiSuggestions && emojiSuggestions.length > 0) {
                formattedText += '<div class="emoji-suggestions mt-2">' +
                    '<small class="text-muted">Quick responses:</small> ';
                
                emojiSuggestions.forEach(emoji => {
                    const emojiId = `emoji-${Math.random().toString(36).substring(2, 10)}`;
                    formattedText += `<span id="${emojiId}" class="emoji-suggestion">${emoji}</span> `;
                    
                    // Add event listeners after DOM is updated
                    setTimeout(() => {
                        const emojiElement = document.getElementById(emojiId);
                        if (emojiElement) {
                            emojiElement.addEventListener('click', function() {
                                sendCustomMessage(emoji);
                            });
                        }
                    }, 100);
                });
                
                formattedText += '</div>';
            }
        }
        
        // Add smart follow-up suggestions if this is a long response
        if (originalText.length > 100 && !formattedText.includes('followup-suggestions')) {
            const followupSuggestions = generateFollowUpSuggestions(originalText);
            
            if (followupSuggestions && followupSuggestions.length > 0) {
                formattedText += '<div class="followup-suggestions mt-3">' +
                    '<small class="text-muted">You might also ask:</small><div class="suggestion-buttons">';
                
                // Create proper buttons for each suggestion
                followupSuggestions.forEach(suggestion => {
                    const buttonId = `suggestion-${Math.random().toString(36).substring(2, 10)}`;
                    formattedText += `<button id="${buttonId}" class="btn btn-sm btn-light suggestion-btn mt-1">${suggestion}</button>`;
                    
                    // We'll add event listeners after the message is added to the DOM
                    setTimeout(() => {
                        const button = document.getElementById(buttonId);
                        if (button) {
                            button.addEventListener('click', function() {
                                sendCustomMessage(suggestion);
                            });
                        }
                    }, 100);
                });
                
                formattedText += '</div></div>';
            }
        }
        
        // Wrap troubleshooting steps in a proper container
        if (formattedText.includes('help you troubleshoot')) {
            const troubleshootingRegex = /(Let me help you troubleshoot:[\s\S]*?)(Did these steps resolve)/;
            formattedText = formattedText.replace(troubleshootingRegex, 
                '<div class="troubleshooting-steps">$1</div>$2');
        }
        
        // Add reaction animation based on message content
        if (originalText.length > 20) {
            const reactionAnimation = getReactionAnimation(originalText);
            if (reactionAnimation) {
                formattedText = `<div class="message-with-reaction ${reactionAnimation}-animation">${formattedText}</div>`;
            }
        }
        
        // Final fallback - replace all remaining newlines with <br> tags that weren't already replaced
        formattedText = formattedText.replace(/\n/g, '<br>');
        
        return formattedText;
    }
    
    // Helper function to get emoji suggestions based on message content
    function getEmojiSuggestions(text) {
        text = text.toLowerCase();
        
        if (text.includes('thank') || text.includes('great') || text.includes('good')) {
            return ['👍', '😊', '🙏'];
        } else if (text.includes('sorry') || text.includes('issue') || text.includes('problem')) {
            return ['😕', '👌', 'Ok'];
        } else if (text.includes('help') || text.includes('can you') || text.includes('how to')) {
            return ['I understand', 'Please continue', 'Tell me more'];
        } else {
            return ['👍', 'Thank you', 'Got it'];
        }
    }
    
    // Helper function to generate follow-up suggestions based on message content
    function generateFollowUpSuggestions(text) {
        text = text.toLowerCase();
        
        const suggestions = [];
        
        if (text.includes('network') || text.includes('connection') || text.includes('internet')) {
            suggestions.push('How can I check my network settings?');
            suggestions.push('What if I reset my router?');
        }
        
        if (text.includes('software') || text.includes('install') || text.includes('update')) {
            suggestions.push('What system requirements are needed?');
            suggestions.push('Is there a manual installation option?');
        }
        
        if (text.includes('account') || text.includes('login') || text.includes('password')) {
            suggestions.push('How can I reset my password?');
            suggestions.push('Is there two-factor authentication?');
        }
        
        if (text.includes('payment') || text.includes('charge') || text.includes('invoice')) {
            suggestions.push('What payment methods do you accept?');
            suggestions.push('How can I update my billing info?');
        }
        
        // Default suggestions if none of the above match
        if (suggestions.length === 0) {
            suggestions.push('Can you explain that in more detail?');
            suggestions.push('What are the next steps?');
            suggestions.push('How long will this take to resolve?');
        }
        
        // Return up to 3 suggestions
        return suggestions.slice(0, 3);
    }
    
    // Helper function to get reaction animation based on message content
    function getReactionAnimation(text) {
        text = text.toLowerCase();
        
        if (text.includes('thank') || text.includes('great') || text.includes('excellent')) {
            return 'celebration';
        } else if (text.includes('sorry') || text.includes('issue') || text.includes('problem')) {
            return 'apologetic';
        } else if (text.includes('urgent') || text.includes('emergency') || text.includes('critical')) {
            return 'quick-response';
        } else if (text.includes('confused') || text.includes('understand') || text.includes('what do you mean')) {
            return 'thinking';
        } else {
            return 'neutral';
        }
    }
    
    // Helper function to send a custom message programmatically
    function sendCustomMessage(message) {
        // Set the message in the input field
        document.getElementById('message-input').value = message;
        
        // Trigger the send button click
        document.getElementById('send-button').click();
    }
    
    // Add a system message when a ticket is created
    function addTicketCreationMessage(ticket) {
        const ticketDiv = document.createElement('div');
        ticketDiv.className = 'message system-message';
        ticketDiv.innerHTML = `
            <p>A support ticket has been created for your issue:</p>
            <div class="card my-2">
                <div class="card-body p-2">
                    <h6 class="card-title">${ticket.ticket_id}: ${ticket.issue_category}</h6>
                    <p class="card-text small">${ticket.description}</p>
                    <span class="badge bg-info">Priority: ${ticket.priority}</span>
                </div>
            </div>
            <p>Our team will review your issue and respond soon.</p>
        `;
        chatContainer.appendChild(ticketDiv);
        
        // Update create ticket button
        createTicketBtn.disabled = true;
        createTicketBtn.textContent = 'Ticket Created';
        
        // Scroll to the bottom
        scrollToBottom();
    }
    
    // Create a ticket from the current chat
    function createTicketFromChat() {
        // Get the last user message as the ticket description
        let description = '';
        for (let i = chatHistory.length - 1; i >= 0; i--) {
            if (chatHistory[i].sender === 'user') {
                description = chatHistory[i].message;
                break;
            }
        }
        
        if (!description) {
            alert('Please provide a description of your issue first.');
            return;
        }
        
        // Show loading
        createTicketBtn.disabled = true;
        createTicketBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
        
        // Send the ticket creation request
        fetch('/api/tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: description,
                initial_message: description
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addTicketCreationMessage(data.ticket);
            } else {
                alert('Error creating ticket: ' + data.message);
                createTicketBtn.disabled = false;
                createTicketBtn.textContent = 'Create Support Ticket';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to create ticket. Please try again.');
            createTicketBtn.disabled = false;
            createTicketBtn.textContent = 'Create Support Ticket';
        });
    }
    
    // Scroll the chat container to the bottom
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Event listeners
    chatForm.addEventListener('submit', sendMessage);
    sendButton.addEventListener('click', sendMessage);
    
    if (createTicketBtn) {
        createTicketBtn.addEventListener('click', createTicketFromChat);
    }
    
    // Initialize the chat
    initChat();
});
