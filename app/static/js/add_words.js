
(function () {
    'use strict';

    /** サーバーから渡される設定（add_words.html で設定） */
    const CONFIG = window.ADD_WORDS_CONFIG || {};
    const SAVE_WORDS_URL = CONFIG.saveWordsUrl || '';
    const DELETE_WORD_BASE_URL = CONFIG.deleteWordBaseUrl || '';
    const DICTIONARY_SHELF_URL = CONFIG.dictionaryShelfUrl || '';
    const CURRENT_PAGE_INDEX = Number(CONFIG.currentPageIndex);
    const BASE_PAGE_URL = CONFIG.basePageUrl || '';
    const PREV_PAGE_URL = CONFIG.prevPageUrl || '';
    const NEXT_PAGE_URL = CONFIG.nextPageUrl || '';
    /** 見開きの片側（左または右）に許容する最大表示行数。サーバーの MAX_LINES_PER_PAGE と一致させる */
    const MAX_LINES_PER_SIDE = Number(CONFIG.maxLinesPerSide) || 23;

    function pageUrl(pageIndex) {
        return BASE_PAGE_URL.replace(/\/0$/, '/' + pageIndex);
    }

    function adjustWordInputWidth(input) {
        const span = document.createElement('span');
        span.style.visibility = 'hidden';
        span.style.position = 'absolute';
        span.style.fontSize = window.getComputedStyle(input).fontSize;
        span.style.fontFamily = window.getComputedStyle(input).fontFamily;
        span.style.fontWeight = window.getComputedStyle(input).fontWeight;
        span.textContent = input.value || input.placeholder || '単語';
        document.body.appendChild(span);

        const width = span.offsetWidth;
        input.style.width = Math.max(48, Math.min(160, width + 13)) + 'px';

        document.body.removeChild(span);
    }

    function setupInputListeners(wordItem) {
        const wordInput = wordItem.querySelector('.word-input');
        const definitionInput = wordItem.querySelector('.definition-input');

        if (wordInput) {
            adjustWordInputWidth(wordInput);
            wordInput.addEventListener('input', () => adjustWordInputWidth(wordInput));
        }
        if (definitionInput) {
            definitionInput.addEventListener('input', () => autoResizeDefinitionTextarea(definitionInput));
        }
    }

    function getVisualLineCount(textarea) {
        const style = window.getComputedStyle(textarea);
        const lineHeight = parseFloat(style.lineHeight);
        return Math.round(textarea.scrollHeight / lineHeight);
    }

    function autoResizeDefinitionTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        const lineCount = getVisualLineCount(textarea);
        const lineCountInput = textarea.closest('.word-item')?.querySelector('.line-count');
        if (lineCountInput) lineCountInput.value = lineCount;
    }


    function createEmptyWordItem() {
        const wordItem = document.createElement('div');
        wordItem.className = 'word-item';
        wordItem.setAttribute('data-word-id', '');
        wordItem.innerHTML = `
            <span class="bracket-open">【</span>
            <input type="hidden" class="line-count" value="0">
            <input type="text" class="word-input" value="" placeholder="単語" data-word-id="">
            <span class="bracket-close">】</span>
            <textarea class="definition-input" placeholder="意味" data-word-id="" rows="2"></textarea>
            <button type="button" class="word-item-delete-btn" title="この単語を削除" aria-label="削除" data-word-id="">×</button>
        `;
        return wordItem;
    }


    function calcItemLines(wordItem) {
        const lineCount = Number(wordItem.querySelector('.line-count')?.value || 0) || 2;
        return 1 + lineCount;
    }

    function calcUsedLines(listEl) {
        if (!listEl) return 0;
        let used = 0;
        listEl.querySelectorAll('.word-item').forEach((item) => {
            used += calcItemLines(item);
        });
        return used;
    }

    function isBlankNewRow(wordItem) {
        const wordIdRaw = wordItem.getAttribute('data-word-id');
        if (wordIdRaw) return false;

        const wordText = (wordItem.querySelector('.word-input')?.value || '').trim();
        const definitionText = (wordItem.querySelector('.definition-input')?.value || '').trim();
        return wordText === '' && definitionText === '';
    }

    function findBlankNewRows() {
        return Array.from(document.querySelectorAll('.word-item')).filter(isBlankNewRow);
    }

    function ensureSingleBlankNewRow() {
        const blanks = findBlankNewRows();
        if (blanks.length <= 1) return;
        blanks.slice(1).forEach((item) => item.remove());
    }

    function chooseTargetListForNewRow() {
        const left = document.getElementById('left-words-list');
        const right = document.getElementById('right-words-list');
        if (!right) return left;

        const leftCount = left?.querySelectorAll('.word-item').length || 0;
        const rightCount = right?.querySelectorAll('.word-item').length || 0;
        return leftCount <= rightCount ? left : right;
    }

    function addNewRow() {
        const blanks = findBlankNewRows();
        if (blanks.length >= 1) {
            ensureSingleBlankNewRow();
            const input = blanks[0].querySelector('.word-input') || blanks[0].querySelector('.definition-input');
            input?.focus();
            return;
        }

        const leftList = document.getElementById('left-words-list');
        const rightList = document.getElementById('right-words-list');
        const newRowLines = 1 + 2; // 単語1行 + 意味2行（初期）
        const leftUsed = calcUsedLines(leftList);
        const rightUsed = calcUsedLines(rightList);

        let targetList = null;
        if (leftUsed + newRowLines <= MAX_LINES_PER_SIDE) {
            targetList = leftList;
        } else if (rightUsed + newRowLines <= MAX_LINES_PER_SIDE) {
            targetList = rightList;
        } else {
            window.location.href = pageUrl(CURRENT_PAGE_INDEX + 1) + '?add=true';
            return;
        }

        const wordItem = createEmptyWordItem();
        targetList.appendChild(wordItem);
        setupInputListeners(wordItem);

        const textarea = wordItem.querySelector('.definition-input');
        if (textarea) autoResizeDefinitionTextarea(textarea);

        const input = wordItem.querySelector('.word-input');
        if (input) input.focus();

        ensureSingleBlankNewRow();
    }

    function collectWordsForSave() {
        const words = [];
        document.querySelectorAll('.word-item').forEach((wordItem) => {
            const wordIdRaw = wordItem.getAttribute('data-word-id');
            const wordId = wordIdRaw ? Number(wordIdRaw) : null;
            const wordInput = wordItem.querySelector('.word-input');
            const definitionInput = wordItem.querySelector('.definition-input');
            const lineCountInput = wordItem.querySelector('.line-count');

            const wordText = (wordInput?.value || '').trim();
            const definitionText = (definitionInput?.value || '').trim();
            const lineCount = Number(lineCountInput?.value || 0) || 2;

            if (!wordId && !wordText) return;

            words.push({
                id: wordId,
                word: wordText,
                definition: definitionText,
                line_count: lineCount
            });
        });
        return words;
    }

    async function saveAllWords({ exitAfterSave }) {
        const saveBtn = document.getElementById('save-button');
        const saveExitBtn = document.getElementById('save-exit-button');

        saveBtn.disabled = true;
        saveExitBtn.disabled = true;

        try {
            const payload = {
                page_index: CURRENT_PAGE_INDEX,
                words: collectWordsForSave()
            };

            const res = await fetch(SAVE_WORDS_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const json = await res.json().catch(() => ({}));
            if (!res.ok || !json.success) {
                throw new Error(json.error || '保存に失敗しました。');
            }

            if (exitAfterSave) {
                window.location.href = DICTIONARY_SHELF_URL;
            } else {
                const nextPage = Number(json.page_index);
                if (Number.isFinite(nextPage) && nextPage >= 0 && nextPage !== CURRENT_PAGE_INDEX) {
                    window.location.href = pageUrl(nextPage);
                } else {
                    window.location.reload();
                }
            }
        } catch (e) {
            alert(e?.message || '保存に失敗しました。');
        } finally {
            saveBtn.disabled = false;
            saveExitBtn.disabled = false;
        }
    }

    function onDeleteButtonClick(e) {
        const btn = e.target.closest('.word-item-delete-btn');
        if (!btn) return;
        e.preventDefault();
        const wordItem = btn.closest('.word-item');
        if (!wordItem) return;
        const wordId = wordItem.getAttribute('data-word-id');

        if (!wordId) {
            wordItem.remove();
            ensureSingleBlankNewRow();
            return;
        }
        if (!confirm('この単語を削除しますか？')) return;

        const url = DELETE_WORD_BASE_URL + '/' + wordId;
        fetch(url, { method: 'POST' })
            .then((res) => res.json())
            .then((json) => {
                if (json.success) {
                    window.location.reload();
                } else {
                    alert(json.error || '削除に失敗しました。');
                }
            })
            .catch(() => alert('削除に失敗しました。'));
    }

    function init() {
        if (!document.getElementById('left-words-list')) return;

        // 既存の全 .word-item に入力リスナーと初期幅・高さを適用
        document.querySelectorAll('.word-item').forEach((wordItem) => {
            setupInputListeners(wordItem);
        });
        document.querySelectorAll('.definition-input').forEach((textarea) => {
            autoResizeDefinitionTextarea(textarea);
        });

        // 保存・保存して終了
        document.getElementById('save-button')?.addEventListener('click', () => {
            saveAllWords({ exitAfterSave: false });
        });
        document.getElementById('save-exit-button')?.addEventListener('click', () => {
            saveAllWords({ exitAfterSave: true });
        });

        // 追加
        document.getElementById('add-row-button')?.addEventListener('click', () => {
            addNewRow();
        });

        // 削除（委譲で動的追加行にも対応）
        document.addEventListener('click', onDeleteButtonClick);

        // ページ送り
        document.getElementById('prev-page-button')?.addEventListener('click', () => {
            window.location.href = PREV_PAGE_URL;
        });
        document.getElementById('next-page-button')?.addEventListener('click', () => {
            window.location.href = NEXT_PAGE_URL;
        });

        // 空欄行は最大1つに整える
        ensureSingleBlankNewRow();

        // ?add=true のときは履歴を残さずURLを消し、空行を1つ追加
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('add') === 'true') {
            window.history.replaceState({}, '', window.location.pathname);
            addNewRow();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
