(function () {
    const config = document.getElementById('shelf-config');
    if (!config) return;

    const baseUrl = config.dataset.baseUrl;
    const favoriteBaseUrl = config.dataset.favoriteBaseUrl.replace(/\/0$/, '');

    const picker = document.getElementById('color-picker');
    const clearBtn = document.getElementById('clear-colors-button');
    const orderBtn = document.getElementById('order-toggle');
    const sortRadios = Array.from(document.querySelectorAll('input[type="radio"][name="sort"]'));
    const favOnlyCheckbox = document.getElementById('fav-only');
    if (!picker || !clearBtn || !orderBtn || sortRadios.length === 0 || !favOnlyCheckbox) return;

    function getSelectedColors() {
        return Array.from(picker.querySelectorAll('.color-dot.selected'))
            .map((btn) => btn.dataset.color)
            .filter(Boolean);
    }

    function getSort() {
        const checked = sortRadios.find((r) => r.checked);
        return checked ? checked.value : 'created';
    }

    function getOrder() {
        const v = (orderBtn.dataset.order || '').trim();
        return (v === 'desc') ? 'desc' : 'asc';
    }

    function navigateWithParams() {
        const params = new URLSearchParams(window.location.search);
        params.set('sort', getSort());
        params.set('order', getOrder());

        params.delete('color');
        getSelectedColors().forEach((c) => params.append('color', c));

        if (favOnlyCheckbox.checked) params.set('fav', '1');
        else params.delete('fav');

        const qs = params.toString();
        window.location.href = baseUrl + (qs ? ('?' + qs) : '');
    }

    sortRadios.forEach((r) => r.addEventListener('change', navigateWithParams));

    picker.addEventListener('click', (e) => {
        const btn = e.target.closest('.color-dot');
        if (!btn) return;
        btn.classList.toggle('selected');
        navigateWithParams();
    });

    clearBtn.addEventListener('click', () => {
        picker.querySelectorAll('.color-dot.selected').forEach((b) => b.classList.remove('selected'));
        navigateWithParams();
    });

    orderBtn.addEventListener('click', () => {
        const next = (getOrder() === 'asc') ? 'desc' : 'asc';
        orderBtn.dataset.order = next;
        orderBtn.textContent = (next === 'desc') ? '▽' : '△';
        navigateWithParams();
    });

    favOnlyCheckbox.addEventListener('change', navigateWithParams);

    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.favorite-toggle');
        if (!btn) return;

        const tile = btn.closest('.dictionary-shelf-tile');
        const dictionaryId = tile?.dataset?.dictionaryId;
        if (!dictionaryId) return;

        try {
            const res = await fetch(favoriteBaseUrl + '/' + dictionaryId, { method: 'POST' });
            const json = await res.json();
            if (!json.success) throw new Error();

            const isFav = !!json.is_favorite;
            btn.dataset.favorite = isFav ? '1' : '0';
            btn.classList.toggle('is-favorite', isFav);

            if (favOnlyCheckbox.checked && !isFav) tile?.remove();
        } catch {
            alert('お気に入りの更新に失敗しました。');
        }
    });
})();