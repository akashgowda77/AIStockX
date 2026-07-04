/**
 * AIStockX - App Module
 * Single responsibility: Application initialization, routing, shared layout
 */

// =============================================================================
// Mobile Sidebar Toggle
// =============================================================================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
    if (overlay) {
        overlay.classList.toggle('show');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
}

// =============================================================================
// Application Initialization (for authenticated pages)
// =============================================================================

function initAuthenticatedPage(pageName) {
    // Check authentication
    if (!requireAuth()) return;

    // Set active nav item
    setActiveNav(pageName);

    // Set page title
    const pageTitle = document.querySelector('.page-title');
    if (pageTitle) {
        pageTitle.textContent = getPageTitle(pageName);
    }

    // Setup navbar with user info
    setupNavbar();
}

function getPageTitle(pageName) {
    const titles = {
        dashboard: 'Dashboard',
        stock: 'Stock Analysis',
        prediction: 'AI Predictions',
        comparison: 'Model Comparison',
    };
    return titles[pageName] || 'AIStockX';
}

function setActiveNav(pageName) {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) {
            item.classList.add('active');
        }
    });
}