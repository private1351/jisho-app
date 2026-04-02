(function () {
    'use strict';

    function adjustWordInputWidth(input) {
        const span = document.createElement('span');
        span.style.visibility = 'hidden';
        span.style.position = 'absolute';
        const cs = window.getComputedStyle(input);
        span.style.fontSize = cs.fontSize;
        span.style.fontFamily = cs.fontFamily;
        span.style.fontWeight = cs.fontWeight;
        span.textContent = input.value || input.placeholder || '単語';
        document.body.appendChild(span);

        const width = span.offsetWidth;
        input.style.width = Math.max(8, Math.min(160, width + 3)) + 'px';

        document.body.removeChild(span);
    }

    function init() {
        document.querySelectorAll('.word-input').forEach((input) => {
            adjustWordInputWidth(input);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

