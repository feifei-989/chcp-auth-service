/**
 * CHCP Frontend Application
 * 
 * Handles:
 * 1. Clerk SDK initialization
 * 2. Auth state management (login/logout)
 * 3. Dashboard data fetching (profile + credits + transactions)
 */

// ============================================================
// Configuration
// ============================================================
const API_BASE = window.location.origin;  // Same origin (Flask serves both)

// ============================================================
// DOM Elements
// ============================================================
const screens = {
    loading: document.getElementById('loading-screen'),
    auth: document.getElementById('auth-screen'),
    dashboard: document.getElementById('dashboard-screen'),
};

const els = {
    clerkAuth: document.getElementById('clerk-auth'),
    logoutBtn: document.getElementById('logout-btn'),
    userAvatar: document.getElementById('user-avatar'),
    userName: document.getElementById('user-name'),
    userEmail: document.getElementById('user-email'),
    userStatus: document.getElementById('user-status'),
    userId: document.getElementById('user-id'),
    userCreated: document.getElementById('user-created'),
    creditsAmount: document.getElementById('credits-amount'),
    transactionsList: document.getElementById('transactions-list'),
    noTransactions: document.getElementById('no-transactions'),
};

// ============================================================
// Screen Management
// ============================================================
function showScreen(name) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    if (screens[name]) {
        screens[name].classList.add('active');
        screens[name].classList.add('fade-in');
    }
}

// ============================================================
// API Calls
// ============================================================
async function apiGet(path, token) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
    if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
    return res.json();
}

// ============================================================
// Dashboard
// ============================================================
async function loadDashboard(session) {
    const token = await session.getToken();

    try {
        // Fetch user profile and transactions in parallel
        const [profileRes, txRes] = await Promise.all([
            apiGet('/api/user/me', token),
            apiGet('/api/user/transactions', token),
        ]);

        if (profileRes.success) {
            renderProfile(profileRes.data);
        }

        if (txRes.success) {
            renderTransactions(txRes.data.transactions);
        }
    } catch (err) {
        console.error('Failed to load dashboard:', err);
    }
}

function renderProfile(user) {
    els.userName.textContent = user.nickname || user.email.split('@')[0];
    els.userEmail.textContent = user.email;

    if (user.avatar_url) {
        els.userAvatar.src = user.avatar_url;
    } else {
        const initial = (user.nickname || user.email)[0].toUpperCase();
        els.userAvatar.src = `https://ui-avatars.com/api/?name=${initial}&background=6366f1&color=fff&size=128`;
    }

    els.userId.textContent = user.id;
    els.creditsAmount.textContent = user.credits;

    if (user.created_at) {
        els.userCreated.textContent = new Date(user.created_at).toLocaleString('zh-CN');
    }

    // Status badge
    if (user.is_active) {
        els.userStatus.textContent = '活跃';
        els.userStatus.className = 'badge badge-active';
    } else {
        els.userStatus.textContent = '已停用';
        els.userStatus.className = 'badge badge-inactive';
    }
}

function renderTransactions(transactions) {
    if (!transactions || transactions.length === 0) {
        els.transactionsList.style.display = 'none';
        els.noTransactions.style.display = 'block';
        return;
    }

    els.noTransactions.style.display = 'none';
    els.transactionsList.style.display = 'flex';

    const actionLabels = {
        'signup_bonus': '🎉 注册赠送',
        'recharge': '💰 充值',
    };

    els.transactionsList.innerHTML = transactions.map(tx => {
        const isPositive = tx.amount >= 0;
        const sign = isPositive ? '+' : '';
        const amountClass = isPositive ? 'positive' : 'negative';
        const label = actionLabels[tx.action] || tx.action;
        const time = new Date(tx.created_at).toLocaleString('zh-CN');

        return `
            <div class="tx-item">
                <div class="tx-info">
                    <span class="tx-action">${label}</span>
                    <span class="tx-desc">${tx.description || ''}</span>
                </div>
                <div style="text-align: right;">
                    <div class="tx-amount ${amountClass}">${sign}${tx.amount}</div>
                    <div class="tx-time">${time}</div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================
// Clerk Initialization
// ============================================================
window.addEventListener('load', async () => {
    // Wait for Clerk to be loaded
    if (!window.Clerk) {
        // Retry a few times
        for (let i = 0; i < 30; i++) {
            await new Promise(r => setTimeout(r, 200));
            if (window.Clerk) break;
        }
    }

    const clerk = window.Clerk;
    if (!clerk) {
        console.error('Clerk SDK failed to load');
        showScreen('auth');
        els.clerkAuth.innerHTML = '<p style="color: #ef4444;">Clerk SDK 加载失败，请检查网络连接</p>';
        return;
    }

    // Wait for Clerk to finish loading
    await clerk.load();

    // Check auth state
    if (clerk.user) {
        // Already signed in → show dashboard
        showScreen('dashboard');
        loadDashboard(clerk.session);
    } else {
        // Not signed in → show auth
        showScreen('auth');
        clerk.mountSignIn(els.clerkAuth, {
            appearance: {
                variables: {
                    colorPrimary: '#6366f1',
                    colorBackground: '#1a1f35',
                    colorText: '#f1f5f9',
                    colorTextSecondary: '#94a3b8',
                    colorInputBackground: '#111827',
                    colorInputText: '#f1f5f9',
                    borderRadius: '12px',
                },
            },
        });
    }

    // Listen for auth state changes
    clerk.addListener(({ session, user }) => {
        if (user && session) {
            // User just signed in
            if (els.clerkAuth.firstChild) {
                clerk.unmountSignIn(els.clerkAuth);
            }
            showScreen('dashboard');
            loadDashboard(session);
        } else {
            // User signed out
            showScreen('auth');
            clerk.mountSignIn(els.clerkAuth, {
                appearance: {
                    variables: {
                        colorPrimary: '#6366f1',
                        colorBackground: '#1a1f35',
                        colorText: '#f1f5f9',
                        colorTextSecondary: '#94a3b8',
                        colorInputBackground: '#111827',
                        colorInputText: '#f1f5f9',
                        borderRadius: '12px',
                    },
                },
            });
        }
    });

    // Logout button
    els.logoutBtn.addEventListener('click', async () => {
        await clerk.signOut();
    });
});
