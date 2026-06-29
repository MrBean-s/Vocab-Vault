
function updateSidebarActive() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('#sidebar .nav-item[data-url]').forEach(item => {
        item.classList.toggle('sidebar-active', item.dataset.url === currentPath);
    });
}

document.getElementById('sidebar').addEventListener('click', (e) => {
    const navItem = e.target.closest('.nav-item[data-url]');
    if (navItem) window.location.href = navItem.dataset.url;
});

document.addEventListener('DOMContentLoaded', updateSidebarActive);
window.addEventListener('pageshow', updateSidebarActive);
