// Theme management for AI Support System
document.addEventListener('DOMContentLoaded', function() {
    // Check if we need to setup theme-toggle in navbar
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Detect current theme from HTML attribute
        const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'dark';
        
        // Update toggle button UI
        updateThemeToggleUI(currentTheme);
        
        // Add event listener for theme toggle
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Update HTML attribute
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            
            // Update toggle button UI
            updateThemeToggleUI(newTheme);
            
            // Save preference if user is logged in
            if (userIsLoggedIn()) {
                saveThemePreference(newTheme);
            }
        });
    }
    
    // Apply emoji animation effects where needed
    setupEmojiAnimations();
});

// Update theme toggle button UI
function updateThemeToggleUI(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    if (theme === 'dark') {
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        themeToggle.setAttribute('title', 'Switch to Light Mode');
        themeToggle.classList.remove('btn-dark');
        themeToggle.classList.add('btn-light');
    } else {
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        themeToggle.setAttribute('title', 'Switch to Dark Mode');
        themeToggle.classList.remove('btn-light');
        themeToggle.classList.add('btn-dark');
    }
}

// Check if user is logged in
function userIsLoggedIn() {
    return document.body.classList.contains('user-logged-in');
}

// Save theme preference via API
function saveThemePreference(theme) {
    fetch('/api/theme-preference', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            theme_preference: theme
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to save theme preference:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving theme preference:', error);
    });
}

// Set up emoji reaction animations
function setupEmojiAnimations() {
    document.querySelectorAll('.emoji-reaction-btn').forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('emoji-pulse');
            setTimeout(() => {
                this.classList.remove('emoji-pulse');
            }, 500);
        });
    });
}

// Load emoji reactions for a specific target
function loadEmojiReactions(targetType, targetId, containerElement) {
    if (!containerElement) return;
    
    fetch(`/api/emoji-reactions/${targetType}/${targetId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.reactions) {
                renderEmojiReactions(data.reactions, containerElement);
            }
        })
        .catch(error => {
            console.error('Error loading emoji reactions:', error);
        });
}

// Render emoji reactions in container
function renderEmojiReactions(reactions, container) {
    if (!container) return;
    
    // Clear existing content
    container.innerHTML = '';
    
    // If no reactions, show empty state
    if (reactions.length === 0) {
        container.innerHTML = '<p class="text-muted small">No reactions yet</p>';
        return;
    }
    
    // Create reaction buttons
    reactions.forEach(reaction => {
        const button = document.createElement('button');
        button.className = `btn btn-sm emoji-reaction-btn me-2 mb-2 ${reaction.reacted_by_current_user ? 'active' : ''}`;
        button.innerHTML = `${reaction.emoji_code} <span class="badge rounded-pill bg-secondary">${reaction.count}</span>`;
        button.setAttribute('data-emoji-code', reaction.emoji_code);
        container.appendChild(button);
    });
}

// Add a new emoji reaction
function addEmojiReaction(emojiCode, targetType, targetId, callback) {
    fetch('/api/emoji-reactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            emoji_code: emojiCode,
            target_type: targetType,
            target_id: targetId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && typeof callback === 'function') {
            callback(data);
        }
    })
    .catch(error => {
        console.error('Error adding emoji reaction:', error);
    });
}