const root = document.documentElement;
const header = document.querySelector('[data-header]');
const themeToggle = document.querySelector('[data-theme-toggle]');
const themeIcon = document.querySelector('[data-theme-icon]');
const menuButton = document.querySelector('[data-menu-button]');
const mobileMenu = document.querySelector('[data-mobile-menu]');
const toast = document.querySelector('[data-toast]');

const storedTheme = localStorage.getItem('saudi-hr-theme');
if (storedTheme === 'light' || storedTheme === 'dark') root.dataset.theme = storedTheme;

function syncThemeIcon() {
  const isDark = root.dataset.theme === 'dark';
  themeIcon.textContent = isDark ? '☼' : '◐';
  themeToggle.setAttribute('aria-label', isDark ? 'تفعيل المظهر الفاتح' : 'تفعيل المظهر الداكن');
}
syncThemeIcon();

themeToggle.addEventListener('click', () => {
  root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('saudi-hr-theme', root.dataset.theme);
  syncThemeIcon();
});

menuButton.addEventListener('click', () => {
  const open = mobileMenu.classList.toggle('is-open');
  menuButton.setAttribute('aria-expanded', String(open));
});
mobileMenu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
  mobileMenu.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
}));

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach((element) => revealObserver.observe(element));

const navLinks = [...document.querySelectorAll('.desktop-nav a')];
const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    navLinks.forEach((link) => link.classList.toggle('is-active', link.hash === `#${entry.target.id}`));
    if (entry.target.id === 'top') header.classList.remove('is-scrolled');
    else header.classList.add('is-scrolled');
  });
}, { rootMargin: '-35% 0px -55% 0px' });
document.querySelectorAll('main section[id]').forEach((section) => sectionObserver.observe(section));

const versionButtons = document.querySelectorAll('[data-version]');
const branchMark = document.querySelector('[data-branch]');
const selectedBranch = document.querySelector('[data-selected-branch]');
versionButtons.forEach((button) => button.addEventListener('click', () => {
  const branch = `version-${button.dataset.version}`;
  versionButtons.forEach((item) => {
    const active = item === button;
    item.classList.toggle('is-active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  branchMark.textContent = branch;
  selectedBranch.textContent = branch;
}));

let toastTimer;
function showToast(message) {
  toast.textContent = message;
  toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 2200);
}

document.querySelector('[data-copy-all]').addEventListener('click', async () => {
  const code = document.querySelector('[data-install-code]').innerText;
  try {
    await navigator.clipboard.writeText(code);
    showToast('تم نسخ أوامر التثبيت');
  } catch {
    showToast('حدد الأوامر وانسخها يدويًا');
  }
});

const checklist = [...document.querySelectorAll('[data-check]')];
const progress = document.querySelector('[data-progress]');
const progressLabel = document.querySelector('[data-progress-label]');
const savedChecks = JSON.parse(localStorage.getItem('saudi-hr-launch-checks') || '[]');
checklist.forEach((item, index) => { item.checked = Boolean(savedChecks[index]); });

function updateChecklist() {
  const states = checklist.map((item) => item.checked);
  const count = states.filter(Boolean).length;
  progress.style.width = `${(count / checklist.length) * 100}%`;
  progressLabel.textContent = `${count} / ${checklist.length}`;
  localStorage.setItem('saudi-hr-launch-checks', JSON.stringify(states));
}
checklist.forEach((item) => item.addEventListener('change', updateChecklist));
updateChecklist();

document.querySelector('[data-year]').textContent = new Date().getFullYear();
