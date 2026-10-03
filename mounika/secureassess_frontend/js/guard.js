import auth from './auth.js';

const guard = {
    /**
     * Require authentication to view this page.
     * Redirects to login if not authenticated.
     */
    requireAuth() {
        if (!auth.isAuthenticated()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    /**
     * Require a specific role.
     * Note: Frontend guards are purely for UX. 
     * The backend must perform real authorization.
     */
    requireRole(requiredRole) {
        if (!this.requireAuth()) return false;

        const user = auth.getUserInfo();
        if (!user) {
            auth.clearSession();
            window.location.href = '/login.html';
            return false;
        }

        if (user.role !== requiredRole && user.role !== 'admin') {
            // Admin can override, otherwise redirect to appropriate dashboard
            this.redirectBasedOnRole(user.role);
            return false;
        }
        return true;
    },

    /**
     * Redirect logged-in users away from auth pages (login/register)
     */
    redirectIfAuthenticated() {
        if (auth.isAuthenticated()) {
            const user = auth.getUserInfo();
            if (user) {
                this.redirectBasedOnRole(user.role);
            }
        }
    },

    /**
     * Helper to route users to their respective dashboards
     */
    redirectBasedOnRole(role) {
        switch (role) {
            case 'student':
                window.location.href = '/dashboard.html';
                break;
            case 'examiner':
                window.location.href = '/examiner.html';
                break;
            case 'admin':
                window.location.href = '/admin.html';
                break;
            default:
                window.location.href = '/index.html';
        }
    }
};

export default guard;
