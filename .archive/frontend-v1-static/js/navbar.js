/**
 * Navigation Bar Component for RAG Enterprise
 * Displays user info and navigation links
 * Version: v8.2.0 (Phase 2)
 */

/**
 * Create and insert navigation bar
 * Call this function at the top of each protected page
 */
function createNavbar() {
    const user = auth.getUser();
    if (!user) return;

    const navbar = document.createElement('div');
    navbar.id = 'app-navbar';
    navbar.innerHTML = `
        <style>
            #app-navbar {
                position: sticky;
                top: 0;
                z-index: 1000;
                background: hsl(var(--background));
                border-bottom: 1px solid hsl(var(--border));
                padding: 12px 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }

            .navbar-left {
                display: flex;
                align-items: center;
                gap: 24px;
            }

            .navbar-logo {
                font-size: 20px;
                font-weight: 700;
                color: hsl(var(--foreground));
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .navbar-logo:hover {
                color: hsl(var(--primary));
            }

            .navbar-nav {
                display: flex;
                gap: 16px;
            }

            .navbar-link {
                color: hsl(var(--muted-foreground));
                text-decoration: none;
                font-size: 14px;
                font-weight: 500;
                padding: 6px 12px;
                border-radius: var(--radius);
                transition: all 0.15s;
            }

            .navbar-link:hover {
                background: hsl(var(--accent));
                color: hsl(var(--accent-foreground));
            }

            .navbar-link.active {
                background: hsl(var(--muted));
                color: hsl(var(--foreground));
            }

            .navbar-right {
                display: flex;
                align-items: center;
                gap: 16px;
            }

            .navbar-user {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 6px 12px;
                background: hsl(var(--card));
                border-radius: var(--radius);
                cursor: pointer;
                transition: background 0.15s;
            }

            .navbar-user:hover {
                background: hsl(var(--muted));
            }

            .navbar-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: hsl(var(--primary));
                display: flex;
                align-items: center;
                justify-content: center;
                color: hsl(var(--primary-foreground));
                font-weight: 600;
                font-size: 14px;
            }

            .navbar-user-info {
                display: flex;
                flex-direction: column;
            }

            .navbar-user-name {
                font-size: 14px;
                font-weight: 600;
                color: hsl(var(--foreground));
            }

            .navbar-user-role {
                font-size: 12px;
                color: hsl(var(--muted-foreground));
            }

            .navbar-logout {
                padding: 8px 16px;
                background: transparent;
                border: 1px solid hsl(var(--border));
                border-radius: var(--radius);
                color: hsl(var(--muted-foreground));
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.15s;
            }

            .navbar-logout:hover {
                background: hsl(var(--accent));
                border-color: hsl(var(--border));
                color: hsl(var(--accent-foreground));
            }

            /* Dropdown menu */
            .navbar-dropdown {
                position: relative;
            }

            .navbar-dropdown-menu {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 8px;
                background: hsl(var(--popover));
                border: 1px solid hsl(var(--border));
                border-radius: var(--radius);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                min-width: 200px;
                display: none;
                z-index: 1001;
            }

            .navbar-dropdown-menu.active {
                display: block;
            }

            .navbar-dropdown-item {
                display: block;
                padding: 12px 16px;
                color: hsl(var(--popover-foreground));
                text-decoration: none;
                font-size: 14px;
                transition: background 0.15s;
                border-bottom: 1px solid hsl(var(--border));
            }

            .navbar-dropdown-item:last-child {
                border-bottom: none;
            }

            .navbar-dropdown-item:hover {
                background: hsl(var(--accent));
            }

            .navbar-dropdown-item.danger {
                color: hsl(var(--destructive));
            }

            .navbar-dropdown-item.danger:hover {
                background: hsl(var(--destructive) / 0.1);
            }

            /* Mobile responsive */
            @media (max-width: 768px) {
                #app-navbar {
                    padding: 10px 16px;
                }

                .navbar-nav {
                    display: none;
                }

                .navbar-user-info {
                    display: none;
                }

                .navbar-logout {
                    padding: 6px 12px;
                    font-size: 13px;
                }
            }
        </style>

        <div class="navbar-left">
            <a href="/chat.html" class="navbar-logo">
                RAG Enterprise
            </a>
            <nav class="navbar-nav">
                <a href="/chat.html" class="navbar-link" data-page="chat">제품 검색</a>
                <a href="/realtime-demo.html" class="navbar-link" data-page="realtime">실시간 데모</a>
            </nav>
        </div>

        <div class="navbar-right">
            <div class="navbar-dropdown">
                <div class="navbar-user" onclick="toggleUserDropdown()">
                    <div class="navbar-avatar">${user.name.charAt(0).toUpperCase()}</div>
                    <div class="navbar-user-info">
                        <span class="navbar-user-name">${user.name}</span>
                        <span class="navbar-user-role">${getRoleDisplayName(user.role)}</span>
                    </div>
                </div>
                <div class="navbar-dropdown-menu" id="userDropdown">
                    <a href="/profile.html" class="navbar-dropdown-item">내 프로필</a>
                    <a href="#" class="navbar-dropdown-item danger" onclick="handleLogout(event)">로그아웃</a>
                </div>
            </div>
        </div>
    `;

    // Insert at the beginning of body
    document.body.insertBefore(navbar, document.body.firstChild);

    // Highlight active page
    highlightActivePage();

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('userDropdown');
        const userButton = document.querySelector('.navbar-user');

        if (dropdown && !userButton.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
}

/**
 * Toggle user dropdown menu
 */
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

/**
 * Handle logout
 */
async function handleLogout(event) {
    if (event) event.preventDefault();

    const confirmed = confirm('로그아웃 하시겠습니까?');
    if (confirmed) {
        await auth.logout();
    }
}

/**
 * Get role display name in Korean
 */
function getRoleDisplayName(role) {
    const roleNames = {
        'admin': '관리자',
        'manager': '매니저',
        'worker': '작업자',
        'viewer': '조회자'
    };
    return roleNames[role] || role;
}

/**
 * Highlight active page link
 */
function highlightActivePage() {
    const currentPage = window.location.pathname.split('/').pop() || 'chat.html';
    const pageKey = currentPage.replace('.html', '');

    const links = document.querySelectorAll('.navbar-link');
    links.forEach(link => {
        const linkPage = link.getAttribute('data-page');
        if (linkPage === pageKey) {
            link.classList.add('active');
        }
    });
}

// Export functions
window.createNavbar = createNavbar;
window.toggleUserDropdown = toggleUserDropdown;
window.handleLogout = handleLogout;
