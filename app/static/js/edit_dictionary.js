const cover = document.getElementById('cover');
const coverColor = document.getElementById('cover-color');
const coverTitle = document.getElementById('cover-title');
const dots = document.querySelectorAll('.color-dot');
const editToggle = document.getElementById('editToggle');
const colorPicker = document.getElementById('colorPicker');
const saveBtn = document.getElementById('saveBtn');
const deleteBtn = document.getElementById('deleteBtn');
const openBtn = document.getElementById('openBtn');
const editNotice = document.getElementById('editNotice');
const viewNotice = document.getElementById('viewNotice');

setViewMode(false);

editToggle.addEventListener('change', () => {
    setViewMode(editToggle.checked);
});

function setViewMode(isEditMode) {
    if (isEditMode) {
        // 編集モード
        coverTitle.removeAttribute('readonly');
        colorPicker.style.display = 'flex';
        saveBtn.style.display = 'inline-block';
        deleteBtn.style.display = 'block';
        editNotice.style.display = 'block';
        openBtn.style.display='none';
        viewNotice.style.display='none';
    } else {
        // 閲覧モード
        coverTitle.setAttribute('readonly', true);
        colorPicker.style.display = 'none';
        saveBtn.style.display = 'none';
        deleteBtn.style.display = 'none';
        editNotice.style.display = 'none';
        openBtn.style.display ='block';
        viewNotice.style.display ='block';
    }
}

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