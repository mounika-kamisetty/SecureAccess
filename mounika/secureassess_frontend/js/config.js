// SecureAssess - Central Configuration
const CONFIG = {
    // Backend API Base URL
    API_BASE_URL: "http://localhost:5000/api/v1",
    
    // Application settings
    APP_NAME: "SecureAssess",
    VERSION: "1.0.0",
    
    // Auth settings
    TOKEN_KEY: "sa_access_token",
    REFRESH_TOKEN_KEY: "sa_refresh_token",
    USER_INFO_KEY: "sa_user_info",
    
    // Risk Levels mapping
    RISK_LEVELS: {
        "low": { color: "text-green-400", bg: "bg-green-500/10", border: "border-green-500/20" },
        "medium": { color: "text-yellow-400", bg: "bg-yellow-500/10", border: "border-yellow-500/20" },
        "high": { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" }
    }
};

export default CONFIG;
