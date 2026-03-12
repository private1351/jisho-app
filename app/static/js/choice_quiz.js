let quizData = [];
let currentIndex = 0;
let canGoNext = false;

document.addEventListener('DOMContentLoaded', () => {
    const nextBtn = document.getElementById('nextBtn');

    nextBtn.addEventListener('click', showNext);

    quizData = JSON.parse(document.getElementById('quiz-data').textContent || '[]');
    if (quizData.length > 0) {
        showQuestion();
    } else {
        document.getElementById('question').textContent = '登録データなし';
    }
});

function showQuestion() {
    canGoNext = false;
    resetJudge();
    document.getElementById('answer').textContent = '';
    updateProgress();

    if (currentIndex >= quizData.length) {
        document.getElementById('quizGrid').style.display = 'none';
        document.getElementById('nextBtn').style.display = 'none';
        document.getElementById('finishMessage').style.display = 'flex';
        return;
    }

    const q = quizData[currentIndex];
    document.getElementById('question').textContent = q.word;

    const container = document.getElementById('choiceButtons');
    container.innerHTML = '';

    q.choices.forEach((choice) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'choice-btn';
        btn.textContent = choice;
        btn.addEventListener('click', () => onChoiceClick(btn, choice, q.correct));
        container.appendChild(btn);
    });
}

function onChoiceClick(btn, choice, correct) {
    if (canGoNext) return;

    const buttons = document.querySelectorAll('#choiceButtons .choice-btn');
    buttons.forEach((b) => {
        b.disabled = true;
        if (b.textContent === correct) {
            b.classList.add('correct');
        }
    });

    if (choice === correct) {
        showCorrect();
        canGoNext = true;
    } else {
        btn.classList.add('wrong');
        showWrong();
        canGoNext = true;
    }

    document.getElementById('answer').textContent = correct;
}

function showNext() {
    currentIndex++;
    showQuestion();
}

const judgeEl = document.getElementById('judge');

function showCorrect() {
    judgeEl.textContent = '正解';
    judgeEl.className = 'judge correct';
}

function showWrong() {
    judgeEl.textContent = '不正解';
    judgeEl.className = 'judge wrong';
}

function resetJudge() {
    judgeEl.textContent = '';
    judgeEl.className = 'judge';
}

function updateProgress() {
    if (quizData.length === 0) return;
    const percent = (currentIndex / quizData.length) * 100;
    document.getElementById('progressFill').style.width = percent + '%';
}
