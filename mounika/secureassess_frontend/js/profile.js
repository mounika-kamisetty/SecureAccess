import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';

guard.requireAuth();

document.addEventListener('DOMContentLoaded', () => {
    const user = auth.getUserInfo();
    
    // Fill navbar links based on role
    const navLinks = document.getElementById('nav-links');
    const dashLink = user.role === 'student' ? 'dashboard.html' : 
                     user.role === 'admin' ? 'admin.html' : 'examiner.html';
                     
    navLinks.innerHTML = `
        <a href="${dashLink}" class="text-slate-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
        <button id="logout-btn" class="text-slate-400 hover:text-red-400 ml-2"><i class="fa-solid fa-sign-out-alt text-xl"></i></button>
    `;
    
    document.getElementById('logout-btn').addEventListener('click', () => auth.logout());

    // Populate user details
    document.getElementById('profile-name').textContent = user.name;
    document.getElementById('profile-email').textContent = user.email;
    document.getElementById('profile-role').textContent = user.role;
    document.getElementById('profile-initial').textContent = user.name.charAt(0).toUpperCase();
    
    // Since we don't have created_at in the basic JWT payload, we fetch full profile
    api.get('/auth/me').then(res => {
        const fullUser = res.data.data.user;
        document.getElementById('profile-id').textContent = fullUser.id;
        document.getElementById('profile-created').textContent = new Date(fullUser.created_at).toLocaleDateString();
    }).catch(e => console.error(e));

    // Handle password change
    const form = document.getElementById('pwd-form');
    const msgDiv = document.getElementById('pwd-msg');
    const btn = document.getElementById('btn-pwd');
    const btnText = document.getElementById('btn-pwd-text');
    const btnLoader = document.getElementById('btn-pwd-loader');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        btn.disabled = true;
        btnText.textContent = "Updating...";
        btnLoader.classList.remove('hidden');
        msgDiv.classList.add('hidden');

        try {
            await api.post('/auth/change-password', {
                current_password: document.getElementById('current-pwd').value,
                new_password: document.getElementById('new-pwd').value
            });
            
            msgDiv.textContent = "Password updated successfully.";
            msgDiv.className = 'mb-4 p-3 rounded-lg text-sm bg-emerald-500/10 border border-emerald-500/20 text-emerald-400';
            msgDiv.classList.remove('hidden');
            form.reset();
            
        } catch (err) {
            msgDiv.textContent = err.response?.data?.message || "Failed to update password.";
            msgDiv.className = 'mb-4 p-3 rounded-lg text-sm bg-red-500/10 border border-red-500/20 text-red-400';
            msgDiv.classList.remove('hidden');
        } finally {
            btn.disabled = false;
            btnText.textContent = "Change Password";
            btnLoader.classList.add('hidden');
        }
    });
});
