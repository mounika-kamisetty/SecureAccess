import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';

guard.requireRole('student');

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('logout-btn').addEventListener('click', () => auth.logout());

    const urlParams = new URLSearchParams(window.location.search);
    const attemptId = urlParams.get('id');
    
    if (!attemptId) {
        window.location.href = 'dashboard.html';
        return;
    }

    try {
        const attemptRes = await api.get(`/attempts/${attemptId}`);
        const attempt = attemptRes.data.data.attempt;
        
        // Wait, students can't get the exam directly to see correct answers, 
        // but they can see title from the exams list. Let's just fetch exams to find the title.
        const examsRes = await api.get('/exams');
        const exam = examsRes.data.data.exams.find(e => e.id === attempt.exam_id);

        if (attempt.status !== 'submitted') {
            // Not submitted yet? Send back to exam or dashboard
            window.location.href = `exam.html?id=${attempt.id}`;
            return;
        }

        renderResult(attempt, exam);

    } catch (e) {
        console.error(e);
        alert("Failed to load result.");
        window.location.href = 'dashboard.html';
    }
});

function renderResult(attempt, exam) {
    document.getElementById('loader').classList.add('hidden');
    document.getElementById('result-content').classList.remove('hidden');

    document.getElementById('res-exam-title').textContent = exam ? exam.title : "Examination";
    document.getElementById('res-date').textContent = `Submitted on: ${new Date(attempt.submitted_at || attempt.updated_at).toLocaleString()}`;
    
    // Animate score counter
    animateCounter('res-score', attempt.score || 0);
    document.getElementById('res-max-score').textContent = attempt.max_score || 0;
    
    // Animate percentage counter
    animateCounter('res-percentage', attempt.percentage || 0);

    // Integrity report
    const badge = document.getElementById('res-risk-badge');
    badge.textContent = (attempt.risk_level || 'LOW').toUpperCase();
    
    if (attempt.risk_level === 'low') {
        badge.className = 'badge badge-success px-3 py-1 text-sm font-bold';
    } else if (attempt.risk_level === 'medium') {
        badge.className = 'badge badge-warning px-3 py-1 text-sm font-bold';
    } else {
        badge.className = 'badge bg-red-500/10 text-red-400 border-red-500/20 px-3 py-1 text-sm font-bold';
    }
    
    document.getElementById('res-risk-score').textContent = `${attempt.risk_score || 0} / 100`;

    // Time Details
    const started = new Date(attempt.start_time || attempt.started_at || attempt.created_at);
    const submitted = new Date(attempt.submitted_at || attempt.updated_at || Date.now());
    const diffMins = Math.round((submitted - started) / 60000);

    document.getElementById('res-started').textContent = started.toLocaleTimeString();
    document.getElementById('res-ended').textContent = submitted.toLocaleTimeString();
    document.getElementById('res-duration').textContent = `${diffMins} minutes`;
}

function animateCounter(elementId, targetValue) {
    const el = document.getElementById(elementId);
    let startTimestamp = null;
    const duration = 1500; // ms
    
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        
        // easeOutQuart
        const easeProgress = 1 - Math.pow(1 - progress, 4);
        const current = (easeProgress * targetValue).toFixed(targetValue % 1 === 0 ? 0 : 1);
        
        el.textContent = current;
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            el.textContent = targetValue;
        }
    };
    
    window.requestAnimationFrame(step);
}
