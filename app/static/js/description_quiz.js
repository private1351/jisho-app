let words = []
let currentIndex = 0
let canGoNext = false;

document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('answerInput');
    const showBtn = document.getElementById('showAnswerBtn');
    const hideBtn = document.getElementById('hideAnswerBtn');
    const nextBtn = document.getElementById('nextBtn');

    showBtn.addEventListener('click', showAnswer)
    hideBtn.addEventListener('click', hideAnswer)
    nextBtn.addEventListener('click', showNext)
    hideBtn.style.display = 'none';

    /* Enterで判定 */
    userInput.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        if (canGoNext){
            showNext();
        } else {
            checkAnswer();
        }
    });

    fetchWord();
})

/* 判定 */
function checkAnswer(){
    if (words.length === 0) return;
    const showBtn = document.getElementById('showAnswerBtn');
    const hideBtn = document.getElementById('hideAnswerBtn');

    const input = document.getElementById('answerInput').value.trim();
    const correct = words[currentIndex].word;

    if (input.toLowerCase() === correct.toLowerCase()){
        showCorrect();
        document.getElementById('answer').textContent = correct;
        showBtn.style.display = 'none';
        hideBtn.style.display = 'inline-block';
        canGoNext = true;
    }
    else {
        showWrong();
        document.getElementById('answer').textContent = correct;
        showBtn.style.display = 'none';
        hideBtn.style.display = 'inline-block';
        canGoNext = false;
    }
}

/* データ取得 */
function fetchWord(){
    const dictId = document.getElementById("dict_id").value;

    fetch('/get-words', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dict_id: dictId })
    })
    .then((response) => response.json())
    .then(data => {
        words = data;
        if (words.length > 0) showQuestion();
        else document.getElementById('question').textContent = "登録データなし"
    })
}

/* 出題 */
function showQuestion(){
    canGoNext = false;
    const showBtn = document.getElementById('showAnswerBtn');
    const hideBtn = document.getElementById('hideAnswerBtn');

    document.getElementById('answer').textContent = "";
    document.getElementById('answerInput').value = "";

    showBtn.style.display = 'inline-block';
    hideBtn.style.display = 'none';
    resetJudge();

    updateProgress();

    if(currentIndex < words.length) {
        document.getElementById('question').textContent = words[currentIndex].definition
    }
    else {
        document.getElementById('quizGrid').style.display = 'none';
        document.getElementById('nextBtn').style.display = 'none';
        document.getElementById("finishMessage").style.display = "flex";
    }
}

/* 答え表示 */
function showAnswer(){
    const showBtn = document.getElementById('showAnswerBtn');
    const hideBtn = document.getElementById('hideAnswerBtn');

    document.getElementById('answer').textContent = words[currentIndex].word
    hideBtn.style.display = 'block';
    showBtn.style.display = 'none';
}

/* 答え非表示 */
function hideAnswer(){
    const showBtn = document.getElementById('showAnswerBtn');
    const hideBtn = document.getElementById('hideAnswerBtn');

    document.getElementById('answer').textContent = ""
    hideBtn.style.display = 'none';
    showBtn.style.display = 'block';
}

/* 次へ */
function showNext(){
    currentIndex++;
    showQuestion();
}

/* 判定UI */
const judge = document.getElementById("judge");

function showCorrect() {
    judge.textContent = "正解";
    judge.className = "judge correct";
}

function showWrong() {
    judge.textContent = "不正解";
    judge.className = "judge wrong";
}

function resetJudge() {
    judge.textContent = "";
    judge.className = "judge";
}

/* 進捗度管理 */
function updateProgress(){
    if (words.length === 0) return;

    const percent = (currentIndex / words.length) * 100;
    document.getElementById("progressFill").style.width = percent + "%";
}