let words = []
let currentIndex = 0
let canGoNext = false;

document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('answerInput');
    const showBtn = document.getElementById('show-answer');
    const nextBtn = document.getElementById('nextBtn');
    const retryBtn = document.getElementById('retryBtn');

    showBtn.addEventListener('click', showAnswer)
    nextBtn.addEventListener('click', showNext)
    retryBtn.style.display = 'none';

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

    const input = document.getElementById('answerInput').value.trim();
    const correct = words[currentIndex].word;

    if (input.toLowerCase() === correct.toLowerCase()){
        showCorrect();
        document.getElementById('answer').textContent = correct;
        canGoNext = true;
    }
    else {
        showWrong();
        document.getElementById('answer').textContent = correct;
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
    document.getElementById('answer').textContent = "";
    document.getElementById('answerInput').value = "";
    resetJudge();

    updateProgress();

    if(currentIndex < words.length) {
        document.getElementById('question').textContent = words[currentIndex].definition
    }
    else {
        document.getElementById('question').textContent = "全問終了！"
        document.getElementById('answerInput').style.display = 'none';
        document.getElementById('nextBtn').style.display = 'none';
        document.getElementById('retryBtn').style.display = 'block';
    }
}

/* 答え表示 */
function showAnswer(){
    document.getElementById('answer').textContent = words[currentIndex].word
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