import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';
import { securityMonitor } from './security.js';

guard.requireRole('student');

// State
let attemptData = null;
let examData = null;
let currentQIndex = 0;
let timerInterval = null;

// UI Elements
const loader = document.getElementById('loader');
const content = document.getElementById('exam-content');
const qNumber = document.getElementById('q-number');
const qText = document.getElementById('q-text');
const qMarks = document.getElementById('q-marks');
const optsContainer = document.getElementById('options-container');
const navGrid = document.getElementById('navigator-grid');
const timerDisplay = document.getElementById('timer-display');
const saveStatus = document.getElementById('save-status');

// Setup global toast
window.showToast = (msg, type='info') => {
    const cont = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'warning' ? 'bg-amber-500/20 border-amber-500/50' :
               type === 'success' ? 'bg-emerald-500/20 border-emerald-500/50' : 'bg-slate-800 border-slate-600';
    const icon = type === 'warning' ? '<i class="fa-solid fa-triangle-exclamation text-amber-400"></i>' :
                 type === 'success' ? '<i class="fa-solid fa-check text-emerald-400"></i>' : '<i class="fa-solid fa-info text-blue-400"></i>';
                 
    toast.className = `toast ${bg} border text-white text-sm`;
    toast.innerHTML = `${icon} <span>${msg}</span>`;
    cont.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
};

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const attemptId = urlParams.get('id');
    
    if (!attemptId) {
        window.location.href = 'exams.html';
        return;
    }

    try {
        // Fetch Attempt and Exam details
        const attemptRes = await api.get(`/attempts/${attemptId}`);
        attemptData = attemptRes.data.data.attempt;
        
        if (attemptData.status === 'submitted') {
            window.location.href = `result.html?id=${attemptId}`;
            return;
        }

        const examRes = await api.get(`/exams/${attemptData.exam_id}`);
        examData = examRes.data.data.exam;

        // Hide the loading spinner, show fullscreen entry overlay
        loader.classList.add('hidden');
        showFullscreenOverlay(attemptId);

    } catch (e) {
        console.error(e);
        alert("Failed to load exam. The session might have expired.");
        window.location.href = 'exams.html';
    }
});

function showFullscreenOverlay(attemptId) {
    const overlay = document.getElementById('fullscreen-overlay');
    overlay.classList.remove('hidden');

    document.getElementById('btn-enter-fullscreen').addEventListener('click', () => {
        // This is a direct user gesture — fullscreen is allowed
        const elem = document.documentElement;
        const goFullscreen = elem.requestFullscreen ||
                             elem.webkitRequestFullscreen ||
                             elem.mozRequestFullScreen ||
                             elem.msRequestFullscreen;

        if (goFullscreen) {
            goFullscreen.call(elem).catch(err => {
                console.warn('Fullscreen failed:', err);
            });
        }

        // Hide overlay, start exam
        overlay.classList.add('hidden');
        startExamUI(attemptId);
    });
}

function startExamUI(attemptId) {
    // Init Security Monitor
    securityMonitor.startMonitoring(attemptId);

    // Build UI
    initNavigator();
    renderQuestion(currentQIndex);
    startTimer();

    // Listeners
    document.getElementById('btn-prev').addEventListener('click', () => {
        if (currentQIndex > 0) renderQuestion(currentQIndex - 1);
    });
    document.getElementById('btn-next').addEventListener('click', () => {
        if (currentQIndex < attemptData.question_order.length - 1) {
            renderQuestion(currentQIndex + 1);
        } else {
            showSubmitModal();
        }
    });
    document.getElementById('btn-clear').addEventListener('click', clearAnswer);
    
    document.getElementById('btn-submit-exam').addEventListener('click', showSubmitModal);
    document.getElementById('modal-cancel-submit').addEventListener('click', () => {
        document.getElementById('submit-modal').classList.add('hidden');
    });
    document.getElementById('modal-confirm-submit').addEventListener('click', submitExam);

    content.classList.remove('hidden');
}

// --- Timer logic ---
function startTimer() {
    let timeLeft = attemptData.remaining_seconds;
    
    function update() {
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            timerDisplay.textContent = "00:00:00";
            timerDisplay.classList.add('text-red-500');
            window.showToast('Time expired! Auto-submitting...', 'warning');
            submitExam(true); // force submit
            return;
        }

        const h = Math.floor(timeLeft / 3600);
        const m = Math.floor((timeLeft % 3600) / 60);
        const s = timeLeft % 60;
        
        timerDisplay.textContent = 
            `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
            
        if (timeLeft < 300) { // < 5 mins
            timerDisplay.classList.add('text-amber-400');
        }

        timeLeft--;
    }
    
    update();
    timerInterval = setInterval(update, 1000);
}

// --- UI Logic ---
function initNavigator() {
    navGrid.innerHTML = '';
    attemptData.question_order.forEach((qId, idx) => {
        const btn = document.createElement('button');
        btn.id = `nav-btn-${idx}`;
        btn.className = 'w-full aspect-square flex items-center justify-center rounded-md text-sm font-medium transition-colors border';
        btn.textContent = idx + 1;
        btn.onclick = () => renderQuestion(idx);
        navGrid.appendChild(btn);
    });
    updateNavigatorUI();
}

function updateNavigatorUI() {
    attemptData.question_order.forEach((qId, idx) => {
        const btn = document.getElementById(`nav-btn-${idx}`);
        const isAnswered = !!attemptData.answers[qId];
        
        if (idx === currentQIndex) {
            btn.className = 'w-full aspect-square flex items-center justify-center rounded-md text-sm font-bold border-2 border-cyan-400 bg-slate-800 text-white';
        } else if (isAnswered) {
            btn.className = 'w-full aspect-square flex items-center justify-center rounded-md text-sm font-medium border border-indigo-400 bg-indigo-500 text-white';
        } else {
            btn.className = 'w-full aspect-square flex items-center justify-center rounded-md text-sm font-medium border border-slate-600 bg-slate-700 text-slate-300 hover:bg-slate-600';
        }
    });
}

function renderQuestion(index) {
    currentQIndex = index;
    const qId = attemptData.question_order[index];

    // Try matching by question_id or id (handle both formats)
    const qdef = examData.questions.find(q => q.question_id === qId || q.id === qId);

    // Safe access to answers — answers may be undefined or empty object
    const answers = attemptData.answers || {};
    const savedEntry = answers[qId];
    const existingAns = savedEntry ? (savedEntry.answer || savedEntry) : null;

    if (!qdef) {
        console.error(`Question ${qId} not found in exam data`, examData.questions);
        qNumber.textContent = `Question ${index + 1} of ${attemptData.question_order.length}`;
        qText.textContent = 'Error: Question data not found. Please contact your examiner.';
        qMarks.textContent = '-';
        optsContainer.innerHTML = '<p class="text-red-400">Could not load question options.</p>';
        return;
    }

    qNumber.textContent = `Question ${index + 1} of ${attemptData.question_order.length}`;
    qText.textContent = qdef.text;
    qMarks.textContent = qdef.marks;
    
    optsContainer.innerHTML = '';
    
    const optionLetters = ['A', 'B', 'C', 'D', 'E'];
    qdef.options.forEach((opt, optIdx) => {
        const isSelected = existingAns === opt;
        
        const label = document.createElement('label');
        label.className = `flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all ${
            isSelected ? 'bg-indigo-500/20 border-indigo-500' : 'bg-slate-800/50 border-slate-700 hover:border-slate-500 hover:bg-slate-800'
        }`;
        
        // Letter badge
        const letter = document.createElement('span');
        letter.className = `shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 ${
            isSelected ? 'bg-indigo-600 border-indigo-400 text-white' : 'bg-slate-800 border-slate-600 text-slate-400'
        }`;
        letter.textContent = optionLetters[optIdx] || optIdx + 1;

        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'current_q';
        radio.value = opt;
        radio.className = 'hidden';
        if (isSelected) radio.checked = true;
        
        radio.addEventListener('change', (e) => handleAnswerSelection(qId, e.target.value));
        
        const textSpan = document.createElement('span');
        textSpan.className = 'text-slate-200 text-base';
        textSpan.textContent = opt;
        
        label.appendChild(radio);
        label.appendChild(letter);
        label.appendChild(textSpan);

        // Click label triggers the radio
        label.addEventListener('click', () => {
            radio.checked = true;
            handleAnswerSelection(qId, opt);
            // Highlight selected
            optsContainer.querySelectorAll('label').forEach(l => {
                l.className = 'flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all bg-slate-800/50 border-slate-700 hover:border-slate-500 hover:bg-slate-800';
                l.querySelector('span.shrink-0').className = 'shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 bg-slate-800 border-slate-600 text-slate-400';
            });
            label.className = 'flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all bg-indigo-500/20 border-indigo-500';
            letter.className = 'shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 bg-indigo-600 border-indigo-400 text-white';
        });

        optsContainer.appendChild(label);
    });
    
    // Buttons state
    document.getElementById('btn-prev').disabled = (index === 0);
    const btnNext = document.getElementById('btn-next');
    if (index === attemptData.question_order.length - 1) {
        btnNext.innerHTML = 'Finish <i class="fa-solid fa-flag-checkered text-sm"></i>';
        btnNext.className = 'btn-danger flex items-center gap-2 px-8 py-2.5';
    } else {
        btnNext.innerHTML = 'Save & Next <i class="fa-solid fa-arrow-right text-sm"></i>';
        btnNext.className = 'btn-primary flex items-center gap-2 px-8 py-2.5';
    }
    
    updateNavigatorUI();
}

async function handleAnswerSelection(questionId, answerValue) {
    // Optimistic UI update
    attemptData.answers[questionId] = answerValue;
    renderQuestion(currentQIndex); // Re-render to highlight selected
    
    saveStatus.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-indigo-400"></i> <span>Saving...</span>';
    
    try {
        await api.put(`/attempts/${attemptData.id}/answer`, {
            question_id: questionId,
            answer: answerValue
        });
        saveStatus.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> <span>Saved</span>';
    } catch (e) {
        console.error(e);
        saveStatus.innerHTML = '<i class="fa-solid fa-triangle-exclamation text-red-400"></i> <span class="text-red-400">Save Failed!</span>';
    }
}

async function clearAnswer() {
    const qId = attemptData.question_order[currentQIndex];
    if (attemptData.answers[qId]) {
        delete attemptData.answers[qId];
        renderQuestion(currentQIndex);
        
        // In a real scenario you'd have a backend endpoint to clear an answer,
        // for now we'll just send an empty string or null if supported, 
        // or just let it stay on the backend and ignore it locally.
        // Actually, API validation requires string >=1. 
        // We will omit actual backend clearing for this demo as we didn't specify it,
        // so it just resets UI. (Production needs a delete endpoint).
    }
}

// --- Submit Logic ---
function showSubmitModal() {
    const answeredCount = Object.keys(attemptData.answers).length;
    const totalCount = attemptData.question_order.length;
    
    document.getElementById('modal-answered').textContent = answeredCount;
    document.getElementById('modal-unanswered').textContent = totalCount - answeredCount;
    
    document.getElementById('submit-modal').classList.remove('hidden');
}

async function submitExam(force = false) {
    // Disable inputs
    document.getElementById('modal-confirm-submit').disabled = true;
    document.getElementById('modal-confirm-submit').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Submitting...';
    
    try {
        // Flush final security events
        await securityMonitor.flushEvents();
        securityMonitor.stopMonitoring();
        
        await api.post(`/attempts/${attemptData.id}/submit`);
        
        // Navigate to results
        window.location.replace(`result.html?id=${attemptData.id}`);
    } catch (e) {
        console.error(e);
        alert("Failed to submit exam! Please contact support.");
        document.getElementById('modal-confirm-submit').disabled = false;
        document.getElementById('modal-confirm-submit').textContent = 'Try Again';
    }
}
