import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';

guard.requireRole('student');

// Global state
let allExams = [];
let allAttempts = [];
let selectedExamId = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('logout-btn').addEventListener('click', () => auth.logout());
    
    // Search filter
    document.getElementById('search-exams').addEventListener('input', (e) => {
        renderExams(e.target.value);
    });

    // Modal listeners
    document.getElementById('modal-cancel').addEventListener('click', closeModal);
    document.getElementById('modal-start-btn').addEventListener('click', startExam);

    loadData();
});

async function loadData() {
    try {
        const [examsRes, attemptsRes] = await Promise.all([
            api.get('/exams'),
            api.get('/attempts/my')
        ]);
        
        allExams = examsRes.data.data.exams;
        allAttempts = attemptsRes.data.data.attempts;
        
        document.getElementById('loader').classList.add('hidden');
        renderExams();
    } catch (e) {
        document.getElementById('loader').classList.add('hidden');
        const sc = document.getElementById('status-container');
        sc.classList.remove('hidden');
        document.getElementById('status-msg').textContent = "Failed to load exams. Please try again later.";
    }
}

function renderExams(searchTerm = '') {
    const grid = document.getElementById('exams-grid');
    const noExams = document.getElementById('no-exams');
    
    grid.innerHTML = '';
    
    const filtered = allExams.filter(ex => 
        ex.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    if (filtered.length === 0) {
        grid.classList.add('hidden');
        noExams.classList.remove('hidden');
        return;
    }
    
    grid.classList.remove('hidden');
    noExams.classList.add('hidden');
    
    filtered.forEach(ex => {
        // Find if attempt exists
        const attempt = allAttempts.find(a => a.exam_id === ex.id);
        
        let statusBadge = `<span class="badge badge-info mb-4 inline-block">Available</span>`;
        let actionBtn = `<button onclick="window.openPreExamModal('${ex.id}')" class="btn-primary w-full py-2">Start Exam</button>`;
        
        if (attempt) {
            if (attempt.status === 'submitted') {
                statusBadge = `<span class="badge badge-success mb-4 inline-block">Completed</span>`;
                actionBtn = `<a href="result.html?id=${attempt.id}" class="btn-secondary w-full py-2 block text-center">View Result</a>`;
            } else if (attempt.status === 'in_progress') {
                statusBadge = `<span class="badge badge-warning mb-4 inline-block">In Progress</span>`;
                actionBtn = `<button onclick="window.openPreExamModal('${ex.id}')" class="btn-primary bg-amber-600 hover:bg-amber-500 w-full py-2 shadow-amber-500/20">Resume Exam</button>`;
            }
        }

        const card = document.createElement('div');
        card.className = 'glass-panel p-6 flex flex-col transform transition duration-200 hover:-translate-y-1 hover:border-indigo-500/50';
        card.innerHTML = `
            <div>
                ${statusBadge}
                <h3 class="text-xl font-bold text-white mb-2 line-clamp-2">${ex.title}</h3>
                <p class="text-sm text-slate-400 mb-4 line-clamp-2">${ex.description || 'No description provided.'}</p>
            </div>
            
            <div class="mt-auto">
                <div class="flex justify-between items-center text-sm text-slate-300 mb-6 bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                    <div class="flex flex-col items-center">
                        <i class="fa-regular fa-clock text-indigo-400 mb-1"></i>
                        <span>${ex.duration} min</span>
                    </div>
                    <div class="flex flex-col items-center border-l border-r border-slate-700 px-4">
                        <i class="fa-solid fa-list-ol text-cyan-400 mb-1"></i>
                        <span>${ex.questions.length} Qs</span>
                    </div>
                    <div class="flex flex-col items-center">
                        <i class="fa-solid fa-star text-amber-400 mb-1"></i>
                        <span>${ex.total_marks} Marks</span>
                    </div>
                </div>
                
                ${actionBtn}
            </div>
        `;
        grid.appendChild(card);
    });
}

// Expose to window for inline onclick attributes
window.openPreExamModal = (examId) => {
    selectedExamId = examId;
    const exam = allExams.find(e => e.id === examId);
    
    document.getElementById('modal-title').textContent = exam.title;
    document.getElementById('modal-duration').textContent = exam.duration;
    document.getElementById('modal-questions').textContent = exam.questions.length;
    
    document.getElementById('start-modal').classList.remove('hidden');
};

function closeModal() {
    selectedExamId = null;
    document.getElementById('start-modal').classList.add('hidden');
}

async function startExam() {
    if (!selectedExamId) return;
    
    const btn = document.getElementById('modal-start-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Initializing...';
    
    try {
        // Hit the start endpoint (creates or fetches in-progress attempt)
        const res = await api.post('/attempts/start', { exam_id: selectedExamId });
        const attempt = res.data.data.attempt;
        
        // Redirect to exam interface with attempt ID
        window.location.href = `exam.html?id=${attempt.id}`;
    } catch (e) {
        alert("Failed to start exam. " + (e.response?.data?.message || ''));
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-play text-sm"></i> Enter Secure Mode';
    }
}
