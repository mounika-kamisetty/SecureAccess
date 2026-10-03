import CONFIG from './config.js';
import auth from './auth.js';

// Setup Axios instance
const api = axios.create({
    baseURL: CONFIG.API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request Interceptor: Attach Token
api.interceptors.request.use(
    (config) => {
        const token = auth.getAccessToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response Interceptor: Handle 401 & Token Refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        // If it's a 401 and we haven't already retried this request
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            // Prevent infinite loops on refresh endpoint itself
            if (originalRequest.url.includes('/auth/refresh')) {
                auth.clearSession();
                window.location.href = '/login.html';
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // Queue requests while refreshing
                return new Promise(function(resolve, reject) {
                    failedQueue.push({resolve, reject});
                }).then(token => {
                    originalRequest.headers['Authorization'] = 'Bearer ' + token;
                    return api(originalRequest);
                }).catch(err => {
                    return Promise.reject(err);
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Attempt to refresh
                const newToken = await auth.refreshToken();
                isRefreshing = false;
                processQueue(null, newToken);
                
                // Retry the original request
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                return api(originalRequest);
            } catch (refreshError) {
                isRefreshing = false;
                processQueue(refreshError, null);
                // Refresh failed, force logout
                auth.clearSession();
                window.location.href = '/login.html?expired=1';
                return Promise.reject(refreshError);
            }
        }

        // Return standard error format
        return Promise.reject(error);
    }
);

export default api;
