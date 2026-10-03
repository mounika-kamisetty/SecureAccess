import auth from './auth.js';
import guard from './guard.js';
import api from './api.js';

guard.requireRole('examiner');

// ─── State ────────────────────────────────────────────────────────────────────
let wizardStep = 1;
let totalQuestions = 0;
let currentQuestionIdx = 0;   // 0-based
let collectedQuestions = [];  // array of filled question objects

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const user = auth.getUserInfo();
    document.getElementById('welcome-text').textContent = `Welcome back, ${user.name}`;
    document.getElementById('logout-btn').addEventListener('click', () => auth.logout());

    loadExams();

    // Modal open/close
    document.getElementById('btn-create-exam').addEventListener('click', openModal);
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-cancel').addEventListener('click', closeModal);

    // Wizard navigation
    document.getElementById('wizard-next').addEventListener('click', handleNext);
    document.getElementById('wizard-prev').addEventListener('click', handlePrev);
    document.getElementById('wizard-save').addEventListener('click', saveExam);

    // Question type toggle
    document.getElementById('q-type-input').addEventListener('change', renderOptionInputs);
});

// ─── Exams List ───────────────────────────────────────────────────────────────
async function loadExams() {
    try {
        const res = await api.get('/exams');
        renderExamsList(res.data.data.exams);
    } catch (e) {
        document.getElementById('exams-container').innerHTML =
            `<p class="text-red-400">Failed to load exams.</p>`;
    }
}

function renderExamsList(exams) {
    const container = document.getElementById('exams-container');
    if (!exams || exams.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-slate-500">
                <i class="fa-solid fa-folder-open text-4xl mb-3"></i>
                <p>No exams yet. Click <strong class="text-emerald-400">Create Exam</strong> to get started.</p>
            </div>`;
        return;
    }

    container.innerHTML = exams.map(ex => {
        const statusBadge = ex.status === 'published'
            ? `<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30">PUBLISHED</span>`
            : `<span class="px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-xs font-bold border border-slate-600">DRAFT</span>`;

        const publishBtn = ex.status === 'draft'
            ? `<button onclick="window.publishExam('${ex.id}')" class="text-emerald-400 text-sm hover:underline ml-4">
                   <i class="fa-solid fa-upload mr-1"></i>Publish
               </button>`
            : '';

        return `
            <div class="p-4 bg-slate-800/50 border border-slate-700 rounded-lg flex flex-col sm:flex-row justify-between sm:items-center gap-4 hover:border-slate-500 transition-colors">
                <div>
                    <div class="flex items-center gap-3 mb-1">
                        <h3 class="font-bold text-white">${ex.title}</h3>
                        ${statusBadge}
                    </div>
                    <p class="text-xs text-slate-400">
                        <i class="fa-solid fa-circle-question mr-1"></i>${ex.questions.length} Questions &nbsp;•&nbsp;
                        <i class="fa-regular fa-clock mr-1"></i>${ex.duration} Mins &nbsp;•&nbsp;
                        <i class="fa-solid fa-star mr-1"></i>${ex.total_marks} Marks
                    </p>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                    ${publishBtn}
                </div>
            </div>`;
    }).join('');
}

window.publishExam = async (examId) => {
    if (!confirm('Publish this exam? Students will be able to take it immediately.')) return;
    try {
        await api.patch(`/exams/${examId}/publish`);
        showToast('Exam published!', 'success');
        loadExams();
    } catch (e) {
        showToast('Failed to publish exam.', 'error');
    }
};

// ─── Modal ────────────────────────────────────────────────────────────────────
function openModal() {
    resetWizard();
    document.getElementById('create-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('create-modal').classList.add('hidden');
    resetWizard();
}

function resetWizard() {
    wizardStep = 1;
    currentQuestionIdx = 0;
    collectedQuestions = [];
    totalQuestions = 0;

    document.getElementById('ex-title').value = '';
    document.getElementById('ex-duration').value = '';
    document.getElementById('ex-num-questions').value = '';
    document.getElementById('ex-desc').value = '';
    document.getElementById('q-save-msg').classList.add('hidden');
    document.getElementById('q-error-msg').classList.add('hidden');

    goToStep(1);
}

// ─── Wizard Navigation ────────────────────────────────────────────────────────
function goToStep(step) {
    wizardStep = step;

    document.getElementById('step-1').classList.toggle('hidden', step !== 1);
    document.getElementById('step-2').classList.toggle('hidden', step !== 2);
    document.getElementById('step-3').classList.toggle('hidden', step !== 3);

    // Progress bar
    const pct = step === 1 ? 33 : step === 2 ? 66 : 100;
    document.getElementById('wizard-progress').style.width = `${pct}%`;

    // Subtitle
    const subtitles = {
        1: 'Step 1 of 3 — Exam Details',
        2: `Step 2 of 3 — Question ${currentQuestionIdx + 1} of ${totalQuestions}`,
        3: 'Step 3 of 3 — Review & Save'
    };
    document.getElementById('wizard-subtitle').textContent = subtitles[step];

    // Buttons
    document.getElementById('wizard-prev').classList.toggle('hidden', step === 1);
    document.getElementById('wizard-next').classList.toggle('hidden', step === 3);
    document.getElementById('wizard-save').classList.toggle('hidden', step !== 3);
}

async function handleNext() {
    if (wizardStep === 1) {
        if (!validateStep1()) return;
        totalQuestions = parseInt(document.getElementById('ex-num-questions').value);
        collectedQuestions = [];
        currentQuestionIdx = 0;
        initQuestionWizard();
        goToStep(2);

    } else if (wizardStep === 2) {
        if (!saveCurrentQuestion()) return;

        currentQuestionIdx++;
        if (currentQuestionIdx < totalQuestions) {
            loadQuestionForm(currentQuestionIdx);
            updateDots();
            document.getElementById('wizard-subtitle').textContent =
                `Step 2 of 3 — Question ${currentQuestionIdx + 1} of ${totalQuestions}`;
        } else {
            // All questions done → review
            renderReview();
            goToStep(3);
        }
    }
}

function handlePrev() {
    if (wizardStep === 2) {
        if (currentQuestionIdx > 0) {
            // Go back one question
            currentQuestionIdx--;
            loadQuestionForm(currentQuestionIdx);
            updateDots();
            document.getElementById('wizard-subtitle').textContent =
                `Step 2 of 3 — Question ${currentQuestionIdx + 1} of ${totalQuestions}`;
        } else {
            goToStep(1);
        }
    } else if (wizardStep === 3) {
        currentQuestionIdx = totalQuestions - 1;
        loadQuestionForm(currentQuestionIdx);
        updateDots();
        goToStep(2);
    }
}

// ─── Step 1 Validation ────────────────────────────────────────────────────────
function validateStep1() {
    const title = document.getElementById('ex-title').value.trim();
    const duration = parseInt(document.getElementById('ex-duration').value);
    const numQ = parseInt(document.getElementById('ex-num-questions').value);

    if (!title) { alert('Please enter an exam title.'); return false; }
    if (!duration || duration < 1) { alert('Please enter a valid duration.'); return false; }
    if (!numQ || numQ < 1 || numQ > 50) { alert('Please enter number of questions (1–50).'); return false; }
    return true;
}

// ─── Question Wizard ──────────────────────────────────────────────────────────
function initQuestionWizard() {
    document.getElementById('q-wizard-total').textContent = totalQuestions;
    renderOptionInputs();
    buildDots();
    loadQuestionForm(0);
}

function buildDots() {
    const nav = document.getElementById('q-dot-nav');
    nav.innerHTML = '';
    for (let i = 0; i < totalQuestions; i++) {
        const dot = document.createElement('div');
        dot.id = `dot-${i}`;
        dot.className = `w-2.5 h-2.5 rounded-full transition-all ${i === 0 ? 'bg-emerald-400 scale-125' : 'bg-slate-600'}`;
        nav.appendChild(dot);
    }
}

function updateDots() {
    for (let i = 0; i < totalQuestions; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (!dot) continue;
        if (i < currentQuestionIdx) {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-600';
        } else if (i === currentQuestionIdx) {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400 scale-125 transition-all';
        } else {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-slate-600 transition-all';
        }
    }
}

function loadQuestionForm(idx) {
    document.getElementById('q-wizard-current').textContent = idx + 1;
    document.getElementById('q-save-msg').classList.add('hidden');
    document.getElementById('q-error-msg').classList.add('hidden');

    // If we already filled this question, pre-populate
    const saved = collectedQuestions[idx];
    if (saved) {
        document.getElementById('q-text-input').value = saved.text;
        document.getElementById('q-marks-input').value = saved.marks;
        document.getElementById('q-type-input').value = saved.type;
    } else {
        document.getElementById('q-text-input').value = '';
        document.getElementById('q-marks-input').value = '5';
        document.getElementById('q-type-input').value = 'mcq';
    }
    renderOptionInputs(saved);
}

function renderOptionInputs(saved = null) {
    const type = document.getElementById('q-type-input').value;
    const isMcq = type === 'mcq';
    const optLabels = isMcq ? ['A', 'B', 'C', 'D'] : ['True', 'False'];
    const list = document.getElementById('options-list');

    list.innerHTML = optLabels.map((lbl, i) => {
        const savedOpt = saved?.options?.[i] || (type === 'true_false' ? lbl : '');
        const isCorrect = saved?.correct_answer === savedOpt;
        return `
            <div class="flex items-center gap-3">
                <input type="radio" name="q-correct-radio" value="${i}"
                    id="opt-radio-${i}" class="w-4 h-4 text-emerald-500 accent-emerald-500"
                    ${isCorrect ? 'checked' : ''}>
                <label for="opt-radio-${i}" class="text-xs font-bold text-emerald-400 w-5 shrink-0">${lbl}</label>
                ${type === 'true_false'
                    ? `<span class="input-field flex-1 text-sm py-1.5 px-3 bg-slate-700/50 cursor-default">${lbl}</span>`
                    : `<input type="text" class="q-opt-text input-field flex-1 text-sm py-1.5" placeholder="Option ${lbl}" value="${savedOpt}">`
                }
            </div>`;
    }).join('');
}

function saveCurrentQuestion() {
    const text = document.getElementById('q-text-input').value.trim();
    const marks = parseInt(document.getElementById('q-marks-input').value);
    const type = document.getElementById('q-type-input').value;
    const errEl = document.getElementById('q-error-msg');

    if (!text) {
        errEl.textContent = 'Please enter the question text.';
        errEl.classList.remove('hidden');
        return false;
    }
    if (!marks || marks < 1) {
        errEl.textContent = 'Please enter valid marks.';
        errEl.classList.remove('hidden');
        return false;
    }

    const isMcq = type === 'mcq';
    const optInputs = document.querySelectorAll('.q-opt-text');
    const options = isMcq
        ? Array.from(optInputs).map(el => el.value.trim())
        : ['True', 'False'];

    if (isMcq && options.some(o => !o)) {
        errEl.textContent = 'Please fill in all 4 options.';
        errEl.classList.remove('hidden');
        return false;
    }

    const selectedRadio = document.querySelector('input[name="q-correct-radio"]:checked');
    if (!selectedRadio) {
        errEl.textContent = 'Please select the correct answer.';
        errEl.classList.remove('hidden');
        return false;
    }

    const correctIdx = parseInt(selectedRadio.value);
    const correctAnswer = options[correctIdx];

    collectedQuestions[currentQuestionIdx] = { text, type, marks, options, correct_answer: correctAnswer };

    document.getElementById('q-save-msg').classList.remove('hidden');
    errEl.classList.add('hidden');
    return true;
}

// ─── Review ───────────────────────────────────────────────────────────────────
function renderReview() {
    const container = document.getElementById('review-container');
    container.innerHTML = collectedQuestions.map((q, i) => `
        <div class="p-3 bg-slate-800 rounded-lg border border-slate-700">
            <div class="flex justify-between items-start gap-2">
                <p class="text-white text-sm font-medium"><span class="text-emerald-400 font-bold mr-2">Q${i+1}.</span>${q.text}</p>
                <span class="text-xs text-slate-400 shrink-0">${q.marks} mk</span>
            </div>
            <p class="text-xs text-slate-400 mt-1">Correct: <span class="text-emerald-400 font-medium">${q.correct_answer}</span></p>
        </div>`).join('');
}

// ─── Save Exam ────────────────────────────────────────────────────────────────
async function saveExam() {
    const payload = {
        title: document.getElementById('ex-title').value.trim(),
        description: document.getElementById('ex-desc').value.trim(),
        duration: parseInt(document.getElementById('ex-duration').value),
        questions: collectedQuestions
    };

    const btn = document.getElementById('wizard-save');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Saving...';

    try {
        await api.post('/exams', payload);
        closeModal();
        showToast('Exam saved as draft!', 'success');
        loadExams();
    } catch (e) {
        showToast('Failed to save exam: ' + (e.response?.data?.message || 'Unknown error'), 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-floppy-disk mr-2"></i>Save as Draft';
    }
}

// ─── Toast ────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'info') {
    const cont = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'error'   ? 'bg-red-500/20 border-red-500/50 text-red-300' :
               type === 'success' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' :
                                    'bg-slate-800 border-slate-600 text-white';
    toast.className = `toast ${bg} border text-sm`;
    toast.textContent = msg;
    cont.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}
