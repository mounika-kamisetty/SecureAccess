# SecureAssess Frontend

A modern, 3D-enhanced frontend for the SecureAssess examination platform.

## Features

- **HTML5 & Vanilla JS**: Lightweight, no build step, easy to understand.
- **Tailwind CSS**: Rapid UI development via CDN.
- **Three.js**: Interactive 3D hero scene for a futuristic feel.
- **Axios**: API communication with token interceptors.
- **Role-Based Dashboards**: Student, Examiner, and Admin views.
- **Distraction-Free Exam UI**: Secure environment with anti-malpractice monitoring.

## Directory Structure

```
secureassess_frontend/
├── index.html          # Landing page (3D Scene)
├── login.html          # Authentication
├── register.html
├── dashboard.html      # Student dashboard
├── exams.html          # Exam list
├── exam.html           # Exam interface
├── result.html         # Post-exam result
├── examiner.html       # Examiner dashboard
├── admin.html          # Admin dashboard
├── profile.html
├── css/
│   └── styles.css      # Custom styles and Tailwind extensions
└── js/
    ├── config.js       # App configuration
    ├── api.js          # Axios setup & interceptors
    ├── auth.js         # Login/logout logic
    ├── guard.js        # Route protection
    ├── security.js     # Anti-malpractice event tracker
    ├── three-scene.js  # 3D landing page logic
    └── [page].js       # Page-specific controllers
```

## Setup & Running

1. **Start the Backend**: Ensure the Flask backend is running on `http://localhost:5000`.
2. **Serve the Frontend**: Use any static file server.
   - Python: `python -m http.server 8000`
   - Node: `npx serve`
3. **Open Browser**: Navigate to `http://localhost:8000`.

## Security Notes

- The frontend implements route guards and UI restrictions.
- **However, the backend is the ultimate authority.**
- Risk scores, exam timers, and final scoring are strictly handled by the Flask API.
