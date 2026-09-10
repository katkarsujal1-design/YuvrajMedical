'use strict';
(() => {
  const root = document.documentElement;
  const key = 'yuvraj-owner-theme';
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let preference;
  try { preference = localStorage.getItem(key); } catch (_) { /* Storage is optional. */ }
  function apply(theme) {
    root.dataset.theme = theme;
    const dark = theme === 'dark';
    const button = document.getElementById('themeToggle');
    if (button) {
      button.setAttribute('aria-pressed', String(dark));
      button.title = dark ? 'Switch to day mode' : 'Switch to night mode';
      document.getElementById('themeIcon').textContent = dark ? '☀' : '☾';
      document.getElementById('themeLabel').textContent = dark ? 'Day mode' : 'Night mode';
    }
    window.dispatchEvent(new Event('owner-theme-change'));
  }
  apply(['light', 'dark'].includes(preference) ? preference : system.matches ? 'dark' : 'light');
  document.addEventListener('DOMContentLoaded', () => {
    apply(root.dataset.theme);
    document.getElementById('themeToggle').addEventListener('click', () => {
      preference = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(key, preference); } catch (_) { /* Keep working without storage. */ }
      apply(preference);
    });
  });
  system.addEventListener('change', () => {
    if (!['light', 'dark'].includes(preference)) apply(system.matches ? 'dark' : 'light');
  });
})();
