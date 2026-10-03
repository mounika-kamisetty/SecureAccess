import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';

guard.requireRole('admin');

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('logout-btn').addEventListener('click', () => auth.logout());
    
    const user = auth.getUserInfo();
    document.getElementById('welcome-text').textContent = `Welcome back, ${user.name}`;

    try {
        const [statsRes, usersRes, logsRes] = await Promise.all([
            api.get('/admin/stats'),
            api.get('/users'),
            api.get('/admin/audit-logs')
        ]);
        
        const stats = statsRes.data.data.stats;
        const users = usersRes.data.data.users;
        const logs = logsRes.data.data.logs;

        renderStats(stats);
        renderUsers(users);
        renderLogs(logs);

    } catch (e) {
        console.error(e);
        alert("Failed to load admin data.");
    }
});

function renderStats(stats) {
    document.getElementById('stat-users').textContent = stats.users.total;
    document.getElementById('stat-exams').textContent = stats.exams.total;
    document.getElementById('stat-attempts').textContent = stats.attempts.total;
    
    // Calculate a dummy avg risk just for display purposes
    document.getElementById('stat-risk').textContent = 'LOW';
    document.getElementById('stat-risk').className = 'text-3xl font-bold text-green-400';
}

function renderUsers(users) {
    const container = document.getElementById('users-container');
    if (users.length === 0) {
        container.innerHTML = '<p class="text-slate-500">No users found.</p>';
        return;
    }
    
    let html = '';
    users.forEach(u => {
        let roleBadge = '';
        if (u.role === 'admin') roleBadge = '<span class="px-2 py-0.5 rounded text-xs bg-purple-500/20 text-purple-400">Admin</span>';
        else if (u.role === 'examiner') roleBadge = '<span class="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">Examiner</span>';
        else roleBadge = '<span class="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">Student</span>';
        
        html += `
            <div class="p-3 bg-slate-800/50 rounded-lg border border-slate-700 mb-3 flex justify-between items-center">
                <div>
                    <p class="font-bold text-white text-sm">${u.name} ${roleBadge}</p>
                    <p class="text-xs text-slate-400">${u.email}</p>
                </div>
                <button class="text-red-400 hover:text-red-300 text-sm" title="Suspend User">
                    <i class="fa-solid fa-ban"></i>
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderLogs(logs) {
    const container = document.getElementById('audit-container');
    if (logs.length === 0) {
        container.innerHTML = '<p class="text-slate-500">No audit logs found.</p>';
        return;
    }
    
    let html = '';
    logs.forEach(log => {
        const date = new Date(log.created_at).toLocaleString();
        html += `
            <div class="p-3 bg-slate-900/50 rounded-lg border-l-2 border-indigo-500 mb-2">
                <div class="flex justify-between items-start mb-1">
                    <span class="font-mono text-xs font-bold text-indigo-400">${log.action}</span>
                    <span class="text-[10px] text-slate-500">${date}</span>
                </div>
                <p class="text-xs text-slate-300">Target: <span class="text-slate-400">${log.target_resource}</span></p>
                <p class="text-xs text-slate-500 mt-1">IP: ${log.ip_address}</p>
            </div>
        `;
    });
    
    container.innerHTML = html;
}
