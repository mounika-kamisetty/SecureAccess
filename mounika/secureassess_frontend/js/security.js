import api from './api.js';

class SecurityMonitor {
    constructor() {
        this.attemptId = null;
        this.isActive = false;
        this.eventBuffer = [];
        this.flushInterval = null;
    }

    /**
     * Start monitoring a specific exam attempt
     */
    startMonitoring(attemptId) {
        this.attemptId = attemptId;
        this.isActive = true;
        this.setupListeners();
        
        // Flush buffer every 10 seconds to avoid spamming the backend
        this.flushInterval = setInterval(() => this.flushEvents(), 10000);
        
        console.log("Security monitoring active for attempt:", attemptId);
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        this.isActive = false;
        this.removeListeners();
        if (this.flushInterval) {
            clearInterval(this.flushInterval);
        }
        this.flushEvents(); // Final flush
    }

    /**
     * Setup DOM event listeners
     */
    setupListeners() {
        // Window blur (tab switch / window minimize)
        this._blurHandler = () => this.recordEvent("window_blur", "Student left the exam window");
        window.addEventListener("blur", this._blurHandler);

        // Visibility change (tab switch)
        this._visibilityHandler = () => {
            if (document.hidden) {
                this.recordEvent("tab_switch", "Student switched browser tabs");
            }
        };
        document.addEventListener("visibilitychange", this._visibilityHandler);

        // Copy
        this._copyHandler = (e) => {
            e.preventDefault();
            this.recordEvent("copy", "Copy action prevented");
            this.showWarningToast("Copying is disabled during the exam.");
        };
        document.addEventListener("copy", this._copyHandler);

        // Paste
        this._pasteHandler = (e) => {
            e.preventDefault();
            this.recordEvent("paste", "Paste action prevented");
            this.showWarningToast("Pasting is disabled during the exam.");
        };
        document.addEventListener("paste", this._pasteHandler);

        // Right Click
        this._contextMenuHandler = (e) => {
            e.preventDefault();
            this.recordEvent("right_click", "Right click prevented");
        };
        document.addEventListener("contextmenu", this._contextMenuHandler);

        // Fullscreen Change
        this._fullscreenHandler = () => {
            if (!document.fullscreenElement) {
                this.recordEvent("fullscreen_exit", "Student exited fullscreen mode");
                this.showWarningToast("You must remain in fullscreen mode!");
            }
        };
        document.addEventListener("fullscreenchange", this._fullscreenHandler);

        // Network Status
        this._offlineHandler = () => {
            this.recordEvent("network_disconnect", "Network connection lost");
            this.showWarningToast("Network connection lost. Reconnecting...");
        };
        window.addEventListener("offline", this._offlineHandler);

        this._onlineHandler = () => {
            this.recordEvent("network_reconnect", "Network connection restored");
            this.showSuccessToast("Network connection restored.");
            // Immediately flush any buffered offline events
            this.flushEvents();
        };
        window.addEventListener("online", this._onlineHandler);
        
        // Keyboard Shortcuts (Ctrl+C, Ctrl+V, F12)
        this._keydownHandler = (e) => {
            if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
                e.preventDefault();
                this.recordEvent("devtools_detected", "Attempt to open developer tools");
                this.showWarningToast("Developer tools are disabled.");
            }
        };
        document.addEventListener("keydown", this._keydownHandler);
    }

    /**
     * Remove DOM event listeners
     */
    removeListeners() {
        window.removeEventListener("blur", this._blurHandler);
        document.removeEventListener("visibilitychange", this._visibilityHandler);
        document.removeEventListener("copy", this._copyHandler);
        document.removeEventListener("paste", this._pasteHandler);
        document.removeEventListener("contextmenu", this._contextMenuHandler);
        document.removeEventListener("fullscreenchange", this._fullscreenHandler);
        window.removeEventListener("offline", this._offlineHandler);
        window.removeEventListener("online", this._onlineHandler);
        document.removeEventListener("keydown", this._keydownHandler);
    }

    /**
     * Request fullscreen mode
     */
    requestFullscreen() {
        const elem = document.documentElement;
        if (elem.requestFullscreen) {
            elem.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable fullscreen: ${err.message}`);
            });
        }
    }

    /**
     * Record an event internally and push to buffer
     */
    recordEvent(eventType, description) {
        if (!this.isActive || !this.attemptId) return;

        const event = {
            attempt_id: this.attemptId,
            event_type: eventType,
            metadata: {
                description: description,
                timestamp: new Date().toISOString(),
                page: window.location.pathname
            }
        };

        this.eventBuffer.push(event);
        
        // If it's a high risk event, flush immediately
        if (["devtools_detected", "tab_switch", "fullscreen_exit"].includes(eventType)) {
            this.flushEvents();
        }
    }

    /**
     * Send buffered events to the backend
     */
    async flushEvents() {
        if (this.eventBuffer.length === 0 || !this.attemptId || !navigator.onLine) return;

        const eventsToSend = [...this.eventBuffer];
        this.eventBuffer = []; // Clear buffer

        try {
            // We could send them in bulk if the backend supports it, 
            // but the current API takes them one by one.
            const promises = eventsToSend.map(event => 
                api.post('/events', event)
            );
            await Promise.allSettled(promises);
        } catch (error) {
            console.error("Failed to sync security events", error);
            // Put them back in the buffer if failed
            this.eventBuffer = [...eventsToSend, ...this.eventBuffer];
        }
    }

    // --- Toast UI Helpers (Relies on external toast function if available) ---
    showWarningToast(msg) {
        if (window.showToast) window.showToast(msg, 'warning');
    }
    
    showSuccessToast(msg) {
        if (window.showToast) window.showToast(msg, 'success');
    }
}

// Export a singleton instance
export const securityMonitor = new SecurityMonitor();
