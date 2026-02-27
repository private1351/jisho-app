const cover = document.getElementById('cover');
const coverColor = document.getElementById('cover-color');
const coverTitle = document.getElementById('cover-title');
const dots = document.querySelectorAll('.color-dot');

// カラーピッカーの処理
dots.forEach(dot => {
    dot.addEventListener('click', () => {
        const colorValue = dot.dataset.color || dot.style.backgroundColor;
        cover.style.backgroundColor = colorValue;
        coverColor.value = colorValue;
        dots.forEach(d => d.classList.remove('selected'));
        dot.classList.add('selected');
    });
});

dots.forEach(dot => {
    dot.style.backgroundColor = dot.dataset.color;
});

// 初期色を現在の設定中の色にする
const initialColor = coverColor.value;
cover.style.backgroundColor = initialColor;

dots.forEach(dot => {
const colorValue = dot.dataset.color || dot.style.backgroundColor;
    if (colorValue === initialColor) {
        dot.classList.add('selected');
    }
});

// textareaの高さを自動調整
function adjustTextareaHeight() {
    coverTitle.style.height = 'auto';
    const scrollHeight = coverTitle.scrollHeight;
    const maxHeight = 80; // max-heightと同じ値
    coverTitle.style.height = Math.min(scrollHeight, maxHeight) + 'px';
}

coverTitle.addEventListener('input', adjustTextareaHeight);
coverTitle.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
    }
});