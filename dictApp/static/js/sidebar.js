const navbar = document.getElementById('navbar');
const navMenu = navbar.querySelector('.nav-menu');
const burgerToggle = navbar.querySelector('#burger-toggle');
const collapseTriggers = navbar.querySelectorAll('.collapse-toggle');

function setSideBarCookie(isCollapsed) {
   document.cookie = `sidebar_collapsed=${isCollapsed}; path=/; max-age=31536000; SameSite=Lax`;
}

function updateSidebarActive() {
   const currentPath = window.location.pathname;
   document.querySelectorAll('#navbar .nav-item[data-url]').forEach(item => {
      item.classList.toggle('active', item.dataset.url === currentPath);
   });
}

document.addEventListener('DOMContentLoaded', () => {
   updateSidebarActive()
   if (window.innerWidth < 1200) {
      navbar.classList.remove('collapsed');
      setSideBarCookie(false);
   }
});

window.addEventListener('pageshow', updateSidebarActive);

burgerToggle.addEventListener('click', () => navMenu.classList.toggle('is-open'));

for (const el of collapseTriggers)
   el.addEventListener('click', () => {
      navbar.classList.toggle('collapsed');
      setSideBarCookie(navbar.classList.contains('collapsed'));
   });

window.addEventListener('resize', () => {
   setTimeout(() => {
      calcModalMargin(document.querySelector('.modal.show'))
      const winWidth = window.innerWidth;
      if (winWidth < 1500 && winWidth > 1200)  navbar.classList.add('collapsed');
      if (winWidth >= 1200) navMenu.classList.remove('is-open');
      if (winWidth >= 1500 || winWidth < 1200) navbar.classList.remove('collapsed');
   }, 50);
});
