// Quantum Edge Analytics - Client-side JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('🧠 Quantum Edge Analytics - Web Interface Loaded');
    
    // Check if we should open a player modal after redirect
    const urlParams = new URLSearchParams(window.location.search);
    const playerId = urlParams.get('player');
    if (playerId) {
        console.log(`Found player parameter in URL: ${playerId}`);
        
        // Remove the parameter from URL without page reload
        const newUrl = window.location.pathname + (window.location.search.replace(/[?&]player=[^&]*/, '').replace(/^&/, '?') || '');
        window.history.replaceState({}, document.title, newUrl.replace(/\?$/, ''));
        
        // Open the modal with a slight delay to ensure page is fully loaded
        setTimeout(() => {
            console.log(`Opening modal for player ${playerId}`);
            openPlayerModal(playerId, 'Player Details');
        }, 300);
    }
    
    // Add global click handler to prevent player navigation
    document.addEventListener('click', function(e) {
        // Check if this is a player navigation attempt
        if (e.target.href && e.target.href.includes('/player/')) {
            console.log('Prevented player navigation attempt:', e.target.href);
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);
    
    // Add click handlers for player rows in matchups page
    initializePlayerRowClicks();
    
    // Add click handlers for clickable players (modal)
    initializeClickablePlayers();
    
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
                // Don't trigger if clicking on specific elements
                if (e.target.tagName.toLowerCase() === 'a' || 
                    e.target.classList.contains('clickable-player') ||
                    e.target.closest('.clickable-player') ||
                    e.target.closest('a')) {
                    console.log('Row click cancelled - clicking on interactive element');
                    return;
                }
                
                console.log('Row clicked - opening modal');
                // For other clicks on the row, open modal
                const playerName = row.querySelector('.clickable-player')?.getAttribute('data-player-name') || 'Unknown Player';
                openPlayerModal(playerId, playerName);
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
 * Initialize click handlers for clickable players (opens modal instead of navigation)
 */
function initializeClickablePlayers() {
    const clickablePlayers = document.querySelectorAll('.clickable-player');
    
    clickablePlayers.forEach(player => {
        const playerId = player.getAttribute('data-player-id');
        const playerName = player.getAttribute('data-player-name');
        
        if (playerId) {
            player.style.cursor = 'pointer';
            player.style.textDecoration = 'underline';
            player.style.color = '#4fc3f7';
            
            // Add event listener in capture phase to prevent other handlers
            player.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                console.log(`Clicked player: ${playerName} (${playerId})`);
                openPlayerModal(playerId, playerName);
                return false;
            }, true); // Use capture phase
            
            // Also add a mousedown event to catch early
            player.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }, true);
            
            // Add hover effect
            player.addEventListener('mouseenter', function() {
                this.style.color = '#29b6f6';
                this.style.fontWeight = 'bold';
            });
            
            player.addEventListener('mouseleave', function() {
                this.style.color = '#4fc3f7';
                this.style.fontWeight = 'normal';
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
            const playerName = e.target.closest('tr').querySelector('.clickable-player')?.getAttribute('data-player-name') || 'Unknown Player';
            openPlayerModal(playerId, playerName);
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

/**
 * Open player modal with stats
 */
function openPlayerModal(playerId, playerName) {
    console.log(`Opening modal for player: ${playerName} (ID: ${playerId})`);
    
    const modal = document.getElementById('playerModal');
    const title = document.getElementById('playerModalTitle');
    const loading = document.getElementById('playerModalLoading');
    const content = document.getElementById('playerModalContent');
    const error = document.getElementById('playerModalError');
    
    // Show modal and loading state
    modal.style.display = 'block';
    title.textContent = playerName || 'Player Details';
    loading.style.display = 'block';
    content.style.display = 'none';
    error.style.display = 'none';
    
    // Fetch player data
    fetch(`/api/player/${playerId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Player data received:', data);
            loading.style.display = 'none';
            content.style.display = 'block';
            populatePlayerModal(data);
        })
        .catch(err => {
            console.error('Error fetching player data:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
            error.innerHTML = `<p>Error loading player data: ${err.message}</p>`;
        });
}

/**
 * Close player modal
 */
function closePlayerModal() {
    const modal = document.getElementById('playerModal');
    modal.style.display = 'none';
}

/**
 * Populate modal with player stats
 */
function populatePlayerModal(playerData) {
    const battingStats = document.getElementById('battingStats');
    const pitchingStats = document.getElementById('pitchingStats');
    const fieldingStats = document.getElementById('fieldingStats');
    
    // Clear existing content
    battingStats.innerHTML = '';
    pitchingStats.innerHTML = '';
    fieldingStats.innerHTML = '';
    
    // Populate batting stats
    if (playerData.stats) {
        const stats = playerData.stats;
        battingStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Games Played:</span>
                <span class="stat-value">${stats.gamesPlayed || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Batting Average:</span>
                <span class="stat-value">${stats.avg || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Home Runs:</span>
                <span class="stat-value">${stats.homeRuns || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">RBI:</span>
                <span class="stat-value">${stats.rbi || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">OPS:</span>
                <span class="stat-value">${stats.ops || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Hits:</span>
                <span class="stat-value">${stats.hits || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Doubles:</span>
                <span class="stat-value">${stats.doubles || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Triples:</span>
                <span class="stat-value">${stats.triples || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Strikeouts:</span>
                <span class="stat-value">${stats.strikeOuts || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Walks:</span>
                <span class="stat-value">${stats.baseOnBalls || 'N/A'}</span>
            </div>
        `;
        
        // Add pitching stats if available
        if (stats.era !== undefined || stats.wins !== undefined) {
            pitchingStats.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">ERA:</span>
                    <span class="stat-value">${stats.era || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Wins:</span>
                    <span class="stat-value">${stats.wins || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Losses:</span>
                    <span class="stat-value">${stats.losses || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">WHIP:</span>
                    <span class="stat-value">${stats.whip || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Strikeouts:</span>
                    <span class="stat-value">${stats.strikeOuts || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Innings Pitched:</span>
                    <span class="stat-value">${stats.inningsPitched || 'N/A'}</span>
                </div>
            `;
        } else {
            pitchingStats.innerHTML = '<p>No pitching statistics available</p>';
        }
        
        // Add basic fielding info
        fieldingStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Position:</span>
                <span class="stat-value">${playerData.position || 'N/A'}</span>
            </div>
        `;
    } else {
        battingStats.innerHTML = '<p>No batting statistics available</p>';
        pitchingStats.innerHTML = '<p>No pitching statistics available</p>';
        fieldingStats.innerHTML = '<p>No fielding statistics available</p>';
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('playerModal');
    if (event.target === modal) {
        closePlayerModal();
    }
}

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
