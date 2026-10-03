import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';

// Guard: Student only
guard.requireRole('student');

document.addEventListener('DOMContentLoaded', async () => {
    // Set welcome text
    const user = auth.getUserInfo();
    document.getElementById('welcome-text').textContent = `Welcome back, ${user.name}`;
    
    // Logout handler
    document.getElementById('logout-btn').addEventListener('click', () => {
        auth.logout();
    });

    try {
        // Fetch exams and attempts concurrently
        const [examsRes, attemptsRes] = await Promise.allSettled([
            api.get('/exams'),
            api.get('/attempts/my')
        ]);

        if (examsRes.status === 'fulfilled' && attemptsRes.status === 'fulfilled') {
            const exams = examsRes.value.data.data.exams;
            const attempts = attemptsRes.value.data.data.attempts;
            
            renderStats(exams, attempts);
            renderAvailableExams(exams, attempts);
            renderRecentResults(attempts, exams);
        } else {
            console.error("Failed to load dashboard data");
        }
    } catch (e) {
        console.error(e);
    }
});

function renderStats(exams, attempts) {
    // Completed exams (submitted status)
    const completedAttempts = attempts.filter(a => a.status === 'submitted');
    
    // Available = Total Published - Completed
    // Note: If an exam has an 'in_progress' attempt, it's technically still available to resume
    const completedExamIds = new Set(completedAttempts.map(a => a.exam_id));
    const availableCount = exams.length - completedExamIds.size;
    
    // Avg Score
    let avgScore = 0;
    if (completedAttempts.length > 0) {
        const totalPercentage = completedAttempts.reduce((sum, a) => sum + (a.percentage || 0), 0);
        avgScore = (totalPercentage / completedAttempts.length).toFixed(1);
    }
    
    // Overall Risk (highest risk among all attempts)
    let highestRiskScore = 0;
    let riskLevel = "LOW";
    let riskColorClass = "text-green-400";
    
    completedAttempts.forEach(a => {
        if (a.risk_score > highestRiskScore) {
            highestRiskScore = a.risk_score;
            riskLevel = a.risk_level.toUpperCase();
        }
    });
    
    if (riskLevel === 'MEDIUM') riskColorClass = 'text-yellow-400';
    if (riskLevel === 'HIGH') riskColorClass = 'text-red-400';

    // Update DOM
    document.getElementById('stat-available').textContent = availableCount;
    document.getElementById('stat-completed').textContent = completedAttempts.length;
    document.getElementById('stat-avg-score').textContent = `${avgScore}%`;
    
    const riskEl = document.getElementById('stat-risk');
    riskEl.textContent = riskLevel;
    riskEl.className = `text-xl font-bold mt-1 ${riskColorClass}`;
}

function renderAvailableExams(exams, attempts) {
    const container = document.getElementById('available-exams-container');
    
    // Filter out submitted exams
    const submittedIds = new Set(attempts.filter(a => a.status === 'submitted').map(a => a.exam_id));
    const available = exams.filter(ex => !submittedIds.has(ex.id)).slice(0, 3); // top 3
    
    if (available.length === 0) {
        container.innerHTML = `
            <div class="text-center py-6">
                <i class="fa-solid fa-check-circle text-3xl text-emerald-500/50 mb-2"></i>
                <p class="text-slate-400">You're all caught up!</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    available.forEach(ex => {
        // Check if there's an in-progress attempt
        const inProgress = attempts.find(a => a.exam_id === ex.id && a.status === 'in_progress');
        const btnText = inProgress ? 'Resume Exam' : 'Start Exam';
        const btnClass = inProgress ? 'btn-secondary text-indigo-400 border-indigo-500/50' : 'btn-primary text-sm py-1.5';
        
        html += `
            <div class="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-slate-500 transition-colors">
                <div>
                    <h3 class="font-bold text-slate-200">${ex.title}</h3>
                    <p class="text-xs text-slate-400 mt-1"><i class="fa-regular fa-clock"></i> ${ex.duration} mins &nbsp;•&nbsp; ${ex.questions.length} Questions</p>
                </div>
                <a href="exams.html" class="${btnClass} px-4">${btnText}</a>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderRecentResults(attempts, exams) {
    const container = document.getElementById('recent-results-container');
    const completed = attempts.filter(a => a.status === 'submitted')
                              .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
                              .slice(0, 3);
                              
    if (completed.length === 0) {
        container.innerHTML = `
            <div class="text-center py-6">
                <i class="fa-solid fa-inbox text-3xl text-slate-600 mb-2"></i>
                <p class="text-slate-400">No results yet.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    completed.forEach(attempt => {
        const exam = exams.find(e => e.id === attempt.exam_id);
        const title = exam ? exam.title : 'Unknown Exam';
        const date = new Date(attempt.updated_at).toLocaleDateString();
        
        let scoreColor = attempt.percentage >= 80 ? 'text-emerald-400' : 
                         attempt.percentage >= 50 ? 'text-amber-400' : 'text-red-400';
        
        html += `
            <div class="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                <div>
                    <h3 class="font-bold text-slate-200">${title}</h3>
                    <p class="text-xs text-slate-400 mt-1">Submitted on ${date}</p>
                </div>
                <div class="text-right">
                    <p class="font-bold text-lg ${scoreColor}">${attempt.percentage.toFixed(1)}%</p>
                    <a href="result.html?id=${attempt.id}" class="text-xs text-indigo-400 hover:underline">View Details</a>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}
