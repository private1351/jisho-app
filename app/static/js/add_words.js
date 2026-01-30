/**
 * 単語登録ページ (add_words) 用スクリプト
 *
 * 役割:
 * - 左/右ページの単語一覧の表示・編集
 * - 単語入力の幅・意味テキストエリアの自動リサイズ
 * - 新規行の追加（左→右→次ページの順で配置）
 * - 一括保存・単語削除・ページ遷移
 *
 * 設定は HTML 側で window.ADD_WORDS_CONFIG に渡すこと。
 */

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

    // -------------------------------------------------------------------------
    // ユーティリティ: ページURL
    // -------------------------------------------------------------------------

    /**
     * 指定したページ番号の単語登録ページURLを返す。
     * BASE_PAGE_URL の末尾が /0 の形式なので、それを pageIndex に置き換えている。
     */
    function pageUrl(pageIndex) {
        return BASE_PAGE_URL.replace(/\/0$/, '/' + pageIndex);
    }

    // -------------------------------------------------------------------------
    // 単語入力フィールドの幅調整
    // -------------------------------------------------------------------------

    /**
     * 単語入力欄の幅を、現在の文字列の表示幅に合わせて調整する。
     * 見えない span で同じフォント・文字列を描画して幅を測り、その幅を input に適用。
     * 最小 60px・最大 200px にクランプする。
     * @param {HTMLInputElement} input - .word-input 要素
     */
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
        input.style.width = Math.max(60, Math.min(200, width + 16)) + 'px';

        document.body.removeChild(span);
    }

    /**
     * 1つの .word-item 内の入力要素にイベントを張る。
     * - 単語入力: input 時に幅を再計算
     * - 意味入力: input 時にテキストエリアの高さを自動リサイズし、行数を .line-count に反映
     * @param {HTMLElement} wordItem - .word-item 要素
     */
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

    // -------------------------------------------------------------------------
    // 意味テキストエリアの行数・高さ
    // -------------------------------------------------------------------------

    /**
     * テキストエリアの現在の表示行数（line-height ベース）を返す。
     */
    function getVisualLineCount(textarea) {
        const style = window.getComputedStyle(textarea);
        const lineHeight = parseFloat(style.lineHeight);
        return Math.round(textarea.scrollHeight / lineHeight);
    }

    /**
     * 意味テキストエリアを内容に合わせて高さを伸縮し、
     * その行数を同じ .word-item 内の .line-count に書き込む。
     * 行数はサーバー側の reflow（ページ割り）で参照されるため、保存時に送信される。
     */
    function autoResizeDefinitionTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        const lineCount = getVisualLineCount(textarea);
        const lineCountInput = textarea.closest('.word-item')?.querySelector('.line-count');
        if (lineCountInput) lineCountInput.value = lineCount;
    }

    // -------------------------------------------------------------------------
    // 新規行の追加・空欄行の管理
    // -------------------------------------------------------------------------

    /**
     * 新規の空の単語行（DOM のみ）を1つ作成する。
     * data-word-id は空。保存時に単語が空なら送信されず、入力があれば新規として保存される。
     */
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

    /**
     * 1つの .word-item が占める「行数」を計算する。
     * 単語1行 + 意味の行数（.line-count、未設定時は2）。
     * サーバー側の MAX_LINES_PER_PAGE と揃えて、左/右の収容量を計算する。
     */
    function calcItemLines(wordItem) {
        const lineCount = Number(wordItem.querySelector('.line-count')?.value || 0) || 2;
        return 1 + lineCount;
    }

    /**
     * 指定したリスト要素（#left-words-list / #right-words-list）内の
     * 全 .word-item の行数の合計を返す。
     */
    function calcUsedLines(listEl) {
        if (!listEl) return 0;
        let used = 0;
        listEl.querySelectorAll('.word-item').forEach((item) => {
            used += calcItemLines(item);
        });
        return used;
    }

    /**
     * 「新規でかつ未入力の空行」かどうかを判定する。
     * data-word-id が空で、単語・意味どちらも空白の行が空欄行。
     */
    function isBlankNewRow(wordItem) {
        const wordIdRaw = wordItem.getAttribute('data-word-id');
        if (wordIdRaw) return false;

        const wordText = (wordItem.querySelector('.word-input')?.value || '').trim();
        const definitionText = (wordItem.querySelector('.definition-input')?.value || '').trim();
        return wordText === '' && definitionText === '';
    }

    /** 画面上の全 .word-item のうち、空欄行だけを配列で返す。 */
    function findBlankNewRows() {
        return Array.from(document.querySelectorAll('.word-item')).filter(isBlankNewRow);
    }

    /**
     * 空欄行が最大1つになるようにする。
     * 2つ以上ある場合は、先頭以外の空欄行を DOM から削除する。
     * 初期表示時や「追加」押下後などで呼び、空行が重複しないようにする。
     */
    function ensureSingleBlankNewRow() {
        const blanks = findBlankNewRows();
        if (blanks.length <= 1) return;
        blanks.slice(1).forEach((item) => item.remove());
    }

    /**
     * 新規行を追加するとき、左と右のどちらのリストに追加するか決める。
     * 右が無い場合は左。ある場合は、現在の項目数が少ない方（同数なら左）を返す。
     */
    function chooseTargetListForNewRow() {
        const left = document.getElementById('left-words-list');
        const right = document.getElementById('right-words-list');
        if (!right) return left;

        const leftCount = left?.querySelectorAll('.word-item').length || 0;
        const rightCount = right?.querySelectorAll('.word-item').length || 0;
        return leftCount <= rightCount ? left : right;
    }

    /**
     * 「追加」ボタンで新しい行を1つ追加する。
     * - 既に空欄行が1つ以上ある場合は、重複を消してその行にフォーカスするだけ。
     * - 左に余裕があれば左、なければ右に追加。両方満杯なら次ページへ遷移し、?add=true で空行を追加する。
     */
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

    // -------------------------------------------------------------------------
    // 保存
    // -------------------------------------------------------------------------

    /**
     * 画面上の全 .word-item から保存用のデータを集める。
     * - 既存行（data-word-id あり）: 空でも含める（編集で空にした場合はサーバーで更新される想定はしていないが送信はする）。
     * - 新規行（data-word-id なし）: 単語が空なら送信しない（空行をDBに作らない）。
     * 返す各要素: { id, word, definition, line_count }
     */
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

    /**
     * 一括保存を実行する。
     * - 保存ボタン・保存して終了ボタンを一時的に無効化。
     * - page_index と words を POST。成功時は exitAfterSave に応じて辞書棚へ戻るか、返ってきた page_index のページへ遷移するか、またはリロード。
     */
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

    // -------------------------------------------------------------------------
    // 単語削除（1単語ずつ）
    // -------------------------------------------------------------------------

    /**
     * 削除ボタンが押されたときの処理。
     * - 新規未保存行（data-word-id が空）: DOM から削除し、空欄行を1つに整えるだけ。
     * - 既存単語: 確認ダイアログのあと、DELETE 用 API を呼び、成功時はリロード。
     */
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

    // -------------------------------------------------------------------------
    // 初期化
    // -------------------------------------------------------------------------

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
