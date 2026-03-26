const favoriteFilter = document.getElementById('favorite-filter');
const selectBox = document.getElementById('dictionary-select');
const colorDots = document.querySelectorAll('.color-dot');

let selectedColor = "";

colorDots.forEach(dot => {
    dot.addEventListener('click', function() {

        if (selectedColor === this.dataset.color) {
            // 同じ色クリック → 解除
            selectedColor = "";
            this.classList.remove('active');
        } else {
            selectedColor = this.dataset.color;

            colorDots.forEach(d => d.classList.remove('active'));
            this.classList.add('active');
        }
        filterDictionaries();
    });
});

function filterDictionaries() {

    const favoriteOnly = favoriteFilter.checked;
    let hasVisible = false;

    for (let option of selectBox.options) {
        if (option.value === "") continue;
        const itemColor = option.dataset.color;
        const isFavorite = option.dataset.favorite === "true";

        let visible = true;
        if (selectedColor && itemColor !== selectedColor) visible = false;
        if (favoriteOnly && !isFavorite) visible = false;
        option.hidden = !visible;
        if (visible) hasVisible = true;
    }
}
favoriteFilter.addEventListener('change', filterDictionaries);

window.addEventListener('DOMContentLoaded', filterDictionaries);

// ▶ PLAY
document.getElementById('quiz-play-btn').onclick = function() {

    const selectedId = selectBox.value;
    const quizType = document.querySelector('input[name="quiz-type"]:checked').value;

    if (!selectedId) {
        alert('辞書を選択してください');
        return;
    }

    window.location.href = '/quiz-play/' + selectedId + '/' + quizType;
};

// ▶ How To
window.addEventListener('load', () => {
    const openButton = document.getElementById('help-open-button');
    const closeButton = document.getElementById('help-close-button');
    const overlay = document.getElementById('help-modal-overlay');
    const modal = document.getElementById('help-modal');

    if (!openButton || !closeButton || !overlay || !modal) return;

    openButton.addEventListener('click', () => {
        modal.classList.remove('hidden');
    });

    closeButton.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    overlay.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            modal.classList.add('hidden');
        }
    });
});