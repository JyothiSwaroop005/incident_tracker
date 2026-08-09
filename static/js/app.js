/**
 * app.js — shared client-side interactivity for the incident tracker.
 * No framework; small, dependency-free enhancements only.
 */

/** Animate stat-card numbers counting up from 0 on page load. */
function animateCounters() {
  const counters = document.querySelectorAll('[data-count]');
  counters.forEach((el) => {
    const target = parseInt(el.getAttribute('data-count'), 10) || 0;
    const duration = 700;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

/** Mobile sidebar toggle. */
function initSidebarToggle() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => sidebar.classList.toggle('open'));

  document.addEventListener('click', (e) => {
    if (
      sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      !toggle.contains(e.target)
    ) {
      sidebar.classList.remove('open');
    }
  });
}

/** Auto-dismiss flash toasts after a few seconds. */
function initToastAutoDismiss() {
  const stack = document.getElementById('toastStack');
  if (!stack) return;
  const toasts = stack.querySelectorAll('.toast-item');
  toasts.forEach((toast, i) => {
    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000 + i * 300);
  });
}

/** Enable Bootstrap tooltips wherever data-bs-toggle="tooltip" is present. */
function initTooltips() {
  const triggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  triggers.forEach((el) => new bootstrap.Tooltip(el));
}

/** Small ripple-on-click effect for primary action buttons. */
function initButtonRipple() {
  const selector = '.btn-gradient, .btn-danger, .btn-success, .btn-outline-secondary, .btn-outline-danger, .btn-ghost';
  document.addEventListener('click', (e) => {
    const btn = e.target.closest(selector);
    if (!btn) return;

    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height);
    ripple.style.position = 'absolute';
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(255,255,255,0.35)';
    ripple.style.transform = 'scale(0)';
    ripple.style.pointerEvents = 'none';
    ripple.style.transition = 'transform 0.5s ease, opacity 0.5s ease';

    const prevPosition = getComputedStyle(btn).position;
    if (prevPosition === 'static') btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);

    requestAnimationFrame(() => { ripple.style.transform = 'scale(1)'; });
    setTimeout(() => { ripple.style.opacity = '0'; }, 250);
    setTimeout(() => ripple.remove(), 550);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initSidebarToggle();
  initToastAutoDismiss();
  initTooltips();
  initButtonRipple();
});
