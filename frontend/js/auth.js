/**
 * AIStockX - Auth Module
 * Single responsibility: Login, Register, Logout, Session management
 */

// =============================================================================
// App Initialization
// =============================================================================

function initApp() {
    // Check auth state on page load
    if (isAuthenticated()) {
        loadUserProfile();
    }
    setupNavbar();
}

// =============================================================================
// Load User Profile
// =============================================================================

async function loadUserProfile() {
    try {
        const response = await authApi.getMe();
        if (response.success && response.data) {
            setUser(response.data);
            updateNavbarUser(response.data);
        }
    } catch (error) {
        // Token expired or invalid
        if (error.status === 401) {
            clearAll();
            if (window.location.pathname.includes('dashboard')) {
                window.location.href = 'login.html';
            }
        }
    }
}

// =============================================================================
// Register
// =============================================================================

async function handleRegister(event) {
    event.preventDefault();

    const form = event.target;
    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    const confirmPassword = form.confirm_password?.value;

    // Client-side validation
    const usernameError = validateUsername(username);
    if (usernameError) {
        showToast(usernameError, 'error');
        return;
    }

    if (!validateEmail(email)) {
        showToast('Please enter a valid email address', 'error');
        return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
        showToast(passwordError, 'error');
        return;
    }

    if (confirmPassword && password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';

    try {
        const response = await authApi.register({ username, email, password });
        showToast('Account created successfully! Please login.', 'success');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1500);
    } catch (error) {
        showToast(getErrorMessage(error), 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Create Account';
    }
}

// =============================================================================
// Login
// =============================================================================

async function handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const username = form.username.value.trim();
    const password = form.password.value;

    if (!username) {
        showToast('Please enter your username or email', 'error');
        return;
    }

    if (!password) {
        showToast('Please enter your password', 'error');
        return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';

    try {
        const response = await authApi.login(username, password);
        setToken(response.access_token);

        // Fetch user profile
        const userResponse = await authApi.getMe();
        if (userResponse.success && userResponse.data) {
            setUser(userResponse.data);
        }

        showToast('Welcome back! Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 500);
    } catch (error) {
        showToast(getErrorMessage(error), 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Sign In';
    }
}

// =============================================================================
// Logout
// =============================================================================

function handleLogout() {
    clearAll();
    showToast('Logged out successfully', 'info');
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 500);
}

// =============================================================================
// Navbar Setup
// =============================================================================

function setupNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const user = getUser();
    const isLoggedIn = isAuthenticated();

    // Check if user menu exists
    let userMenu = navbar.querySelector('.navbar-user');

    if (!isLoggedIn) {
        if (userMenu) userMenu.remove();
        return;
    }

    if (!userMenu) {
        const navRight = navbar.querySelector('.navbar-right') || navbar;
        userMenu = document.createElement('div');
        userMenu.className = 'navbar-user';
        navRight.appendChild(userMenu);
    }

    updateNavbarUser(user);
}

function updateNavbarUser(user) {
    const userMenu = document.querySelector('.navbar-user');
    if (!userMenu) return;

    const username = user && user.username ? user.username : 'User';
    const initial = username.charAt(0).toUpperCase();
    const email = user && user.email ? user.email : '';

    userMenu.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <div class="user-dropdown">
                <button class="user-dropdown-trigger" onclick="toggleDropdown(event)">
                    <div class="user-avatar">${initial}</div>
                    <span class="user-name">${username}</span>
                    <i class="fas fa-chevron-down dropdown-arrow"></i>
                </button>
                <div class="dropdown-menu" id="userDropdown">
                    <div class="dropdown-header">
                        <span class="dropdown-user-name">${username}</span>
                        ${email ? `<span class="dropdown-user-email">${email}</span>` : ''}
                    </div>
                    <div class="dropdown-divider"></div>
                    <a href="dashboard.html" class="dropdown-item">
                        <i class="fas fa-chart-line"></i> Dashboard
                    </a>
                    <div class="dropdown-divider"></div>
                    <button class="dropdown-item dropdown-item-danger" onclick="handleLogout()">
                        <i class="fas fa-sign-out-alt"></i> Sign Out
                    </button>
                </div>
            </div>
            <button class="btn-navbar-logout" onclick="handleLogout()" title="Sign Out / Logout">
                <i class="fas fa-sign-out-alt"></i> <span>Sign Out</span>
            </button>
        </div>
    `;

    setupSidebarLogout();
}

function setupSidebarLogout() {
    const sidebarNav = document.querySelector('.sidebar-nav');
    if (!sidebarNav || sidebarNav.querySelector('.nav-item-logout')) return;

    const accountSection = document.createElement('div');
    accountSection.className = 'nav-section';
    accountSection.style.marginTop = '24px';
    accountSection.textContent = 'Account';

    const logoutBtn = document.createElement('button');
    logoutBtn.className = 'nav-item nav-item-logout';
    logoutBtn.onclick = handleLogout;
    logoutBtn.title = 'Sign Out';
    logoutBtn.innerHTML = `
        <i class="fas fa-sign-out-alt"></i>
        <span>Sign Out</span>
    `;

    sidebarNav.appendChild(accountSection);
    sidebarNav.appendChild(logoutBtn);
}

function toggleDropdown(event) {
    event.stopPropagation();
    const menu = document.getElementById('userDropdown');
    if (menu) {
        menu.classList.toggle('show');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function () {
    const menus = document.querySelectorAll('.dropdown-menu.show');
    menus.forEach(menu => menu.classList.remove('show'));
});

// =============================================================================
// Login Page Init
// =============================================================================

function initLoginPage() {
    if (redirectIfAuthenticated()) return;

    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', handleLogin);
    }
}

// =============================================================================
// Register Page Init
// =============================================================================

function initRegisterPage() {
    if (redirectIfAuthenticated()) return;

    const form = document.getElementById('registerForm');
    if (form) {
        form.addEventListener('submit', handleRegister);
    }
}