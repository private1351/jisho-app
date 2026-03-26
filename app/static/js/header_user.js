window.addEventListener('load', () => {
    const openButton = document.getElementById('user-menu-open');
    const closeButton = document.getElementById('user-modal-close');
    const overlay = document.getElementById('user-modal-overlay');
    const modal = document.getElementById('user-modal');

    if (!openButton || !closeButton || !overlay || !modal) return;

    function openModal() {
        modal.classList.remove('hidden');
    }

    function closeModal() {
        modal.classList.add('hidden');
    }

    openButton.addEventListener('click', openModal);
    closeButton.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
});