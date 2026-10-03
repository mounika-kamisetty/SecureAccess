import CONFIG from './config.js';

const auth = {
    /**
     * Get the current access token
     */
    getAccessToken() {
        return localStorage.getItem(CONFIG.TOKEN_KEY) || sessionStorage.getItem(CONFIG.TOKEN_KEY);
    },

    /**
     * Get the current refresh token
     */
    getRefreshToken() {
        return localStorage.getItem(CONFIG.REFRESH_TOKEN_KEY) || sessionStorage.getItem(CONFIG.REFRESH_TOKEN_KEY);
    },

    /**
     * Get user info
     */
    getUserInfo() {
        const userStr = localStorage.getItem(CONFIG.USER_INFO_KEY) || sessionStorage.getItem(CONFIG.USER_INFO_KEY);
        return userStr ? JSON.parse(userStr) : null;
    },

    /**
     * Set session data
     */
    setSession(tokens, user, remember = false) {
        const storage = remember ? localStorage : sessionStorage;
        
        storage.setItem(CONFIG.TOKEN_KEY, tokens.access_token);
        storage.setItem(CONFIG.REFRESH_TOKEN_KEY, tokens.refresh_token);
        storage.setItem(CONFIG.USER_INFO_KEY, JSON.stringify(user));
    },

    /**
     * Clear all session data
     */
    clearSession() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.REFRESH_TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_INFO_KEY);
        sessionStorage.removeItem(CONFIG.TOKEN_KEY);
        sessionStorage.removeItem(CONFIG.REFRESH_TOKEN_KEY);
        sessionStorage.removeItem(CONFIG.USER_INFO_KEY);
    },

    /**
     * Login request
     */
    async login(email, password, remember = false) {
        try {
            const response = await axios.post(`${CONFIG.API_BASE_URL}/auth/login`, {
                email,
                password
            });
            
            if (response.data.success) {
                const data = response.data.data;
                this.setSession(
                    { access_token: data.access_token, refresh_token: data.refresh_token },
                    data.user,
                    remember
                );
                return { success: true, role: data.user.role };
            }
        } catch (error) {
            return { 
                success: false, 
                message: error.response?.data?.message || 'Login failed' 
            };
        }
    },

    /**
     * Register request
     */
    async register(name, email, password, role) {
        try {
            const response = await axios.post(`${CONFIG.API_BASE_URL}/auth/register`, {
                name,
                email,
                password,
                role
            });
            
            return { success: true };
        } catch (error) {
            return { 
                success: false, 
                message: error.response?.data?.message || 'Registration failed' 
            };
        }
    },

    /**
     * Logout request
     */
    async logout() {
        try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
                await axios.post(
                    `${CONFIG.API_BASE_URL}/auth/logout`, 
                    { refresh_token: refreshToken },
                    { headers: { Authorization: `Bearer ${this.getAccessToken()}` } }
                );
            }
        } catch (e) {
            console.error('Logout error on server', e);
        } finally {
            this.clearSession();
            window.location.href = '/login.html';
        }
    },

    /**
     * Refresh Token request
     */
    async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) throw new Error("No refresh token available");

        const response = await axios.post(`${CONFIG.API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
        });

        if (response.data.success) {
            const data = response.data.data;
            const user = this.getUserInfo();
            // Update storage where it was originally saved
            const storage = localStorage.getItem(CONFIG.REFRESH_TOKEN_KEY) ? localStorage : sessionStorage;
            storage.setItem(CONFIG.TOKEN_KEY, data.access_token);
            if (data.refresh_token) {
                storage.setItem(CONFIG.REFRESH_TOKEN_KEY, data.refresh_token);
            }
            return data.access_token;
        } else {
            throw new Error("Refresh failed");
        }
    },
    
    /**
     * Utility to check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getAccessToken();
    }
};

export default auth;
