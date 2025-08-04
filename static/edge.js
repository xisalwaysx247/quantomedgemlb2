// Quantum Edge Analytics - Client-side JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('🧠 Quantum Edge Analytics - Web Interface Loaded');
    
    // Add click handlers for player rows in matchups page
    initializePlayerRowClicks();
    
    // Add smooth scrolling for anchor links
    initializeSmoothScrolling();
    
    // Initialize any other interactive features
    initializeTooltips();
});

/**
 * Initialize click handlers for player rows
 * Allows clicking anywhere on a hitter row to navigate to player page
 */
function initializePlayerRowClicks() {
    const playerRows = document.querySelectorAll('tr[data-player-id]');
    
    playerRows.forEach(row => {
        const playerId = row.getAttribute('data-player-id');
        
        if (playerId) {
            row.style.cursor = 'pointer';
            
            row.addEventListener('click', function(e) {
                // Don't trigger if clicking on a link
                if (e.target.tagName.toLowerCase() === 'a') {
                    return;
                }
                
                viewPlayer(playerId);
            });
            
            // Add hover effect
            row.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.02)';
                this.style.transition = 'transform 0.2s ease';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        }
    });
}

/**
 * Navigate to player page
 * @param {number|string} playerId - The MLB player ID
 */
function viewPlayer(playerId) {
    if (playerId) {
        window.location.href = `/player/${playerId}`;
    }
}

/**
 * Navigate to team page
 * @param {number|string} teamId - The MLB team ID
 */
function viewTeam(teamId) {
    if (teamId) {
        window.location.href = `/team/${teamId}`;
    }
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize tooltips and enhanced interactions
 */
function initializeTooltips() {
    // Add tooltips for tier badges
    const tierCells = document.querySelectorAll('.tier-cell');
    
    tierCells.forEach(cell => {
        const tier = cell.textContent.trim();
        let tooltip = '';
        
        switch(tier) {
            case '🟢':
                tooltip = 'Strong Hitter - Above average performance';
                break;
            case '🟡':
                tooltip = 'Bubble Hitter - Average performance';
                break;
            case '🔴':
                tooltip = 'Weak Hitter - Below average performance';
                break;
            case '❓':
                tooltip = 'No Data Available';
                break;
        }
        
        if (tooltip) {
            cell.setAttribute('title', tooltip);
        }
    });
    
    // Add hover effects for stat boxes
    const statBoxes = document.querySelectorAll('.stat-box');
    statBoxes.forEach(box => {
        box.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.transition = 'transform 0.2s ease';
        });
        
        box.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Utility function to format numbers with appropriate precision
 * @param {number|string} value - The value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted value
 */
function formatStat(value, decimals = 3) {
    if (value === null || value === undefined || value === 'N/A') {
        return 'N/A';
    }
    
    const num = parseFloat(value);
    if (isNaN(num)) {
        return 'N/A';
    }
    
    return num.toFixed(decimals);
}

/**
 * Add keyboard navigation support
 */
document.addEventListener('keydown', function(e) {
    // ESC key to go back
    if (e.key === 'Escape') {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/';
        }
    }
    
    // Enter key on focused player rows
    if (e.key === 'Enter' && e.target.closest('tr[data-player-id]')) {
        const playerId = e.target.closest('tr').getAttribute('data-player-id');
        if (playerId) {
            viewPlayer(playerId);
        }
    }
});

/**
 * Add loading states for navigation
 */
function showLoading() {
    document.body.style.cursor = 'wait';
}

function hideLoading() {
    document.body.style.cursor = 'default';
}

// Add loading states to navigation links
document.addEventListener('click', function(e) {
    if (e.target.tagName.toLowerCase() === 'a' && e.target.href) {
        // Only show loading for internal links
        if (e.target.href.startsWith(window.location.origin)) {
            showLoading();
            
            // Hide loading after a short delay if page doesn't load
            setTimeout(hideLoading, 3000);
        }
    }
});

// Hide loading when page loads
window.addEventListener('load', hideLoading);

// Console branding
console.log(`
 ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗████████╗██╗   ██╗███╗   ███╗
██╔═══██╗██║   ██║██╔══██╗████╗  ██║╚══██╔══╝██║   ██║████╗ ████║
██║   ██║██║   ██║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
██║▄▄ ██║██║   ██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝

🧠✨ Quantum Edge Analytics - Web Interface
Advanced MLB Intelligence • Market Analysis • Predictive Insights
`);
