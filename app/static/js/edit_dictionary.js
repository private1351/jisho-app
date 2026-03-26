const cover = document.getElementById('cover');
const coverColor = document.getElementById('cover-color');
const coverTitle = document.getElementById('cover-title');
const dots = document.querySelectorAll('.color-dot');
const colorPicker = document.getElementById('colorPicker');
const saveBtn = document.getElementById('saveBtn');
const deleteBtn = document.getElementById('deleteBtn');
const openBtn = document.getElementById('openBtn');
const editNotice = document.getElementById('editNotice');
const privacyToggle = document.getElementById('privacyToggle');
const isPrivateInput = document.getElementById('isPrivate');

/** サーバー初期値（hidden）に合わせる */
let isPrivate = !!(isPrivateInput && isPrivateInput.value === 'true');

function applyPrivacyVisualState() {
    const icon = document.getElementById('lockIcon');
    const text = document.getElementById('privacyText');
    if (!icon || !text) return;
    if (isPrivate) {
        icon.classList.remove('fa-lock-open');
        icon.classList.add('fa-lock');
        text.textContent = 'PRIVATE';
    } else {
        icon.classList.remove('fa-lock');
        icon.classList.add('fa-lock-open');
        text.textContent = 'PUBLIC';
    }
}

applyPrivacyVisualState();

// 辞書詳細は常に編集画面として扱う
if (coverTitle) coverTitle.removeAttribute('readonly');
if (colorPicker) colorPicker.style.display = 'flex';
if (saveBtn) saveBtn.style.display = 'inline-block';
if (deleteBtn) deleteBtn.style.display = 'inline-block';
if (openBtn) openBtn.style.display = 'inline-block';
if (editNotice) editNotice.style.display = 'block';
if (privacyToggle) privacyToggle.style.display = 'flex';

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

function togglePrivacy() {
    const input = document.getElementById("isPrivate");
    isPrivate = !isPrivate;
    if (input) input.value = isPrivate ? "true" : "false";
    applyPrivacyVisualState();
}