(() => {
  'use strict';

  const DEBOUNCE_MS = 300;

  document.querySelectorAll('[data-like-form]').forEach((form) => {
    const button = form.querySelector('button');
    const icon = form.querySelector('[data-like-icon]');
    const label = form.querySelector('[data-like-label]');
    const status = form.querySelector('[data-like-status]');
    let saved = button.getAttribute('aria-pressed') === 'true';
    let desired = saved;
    let timer;
    let inFlight = false;
    let ready = false;

    function paint(message = '') {
      button.setAttribute('aria-pressed', String(desired));
      button.value = String(!desired);
      button.classList.toggle('is-liked', desired);
      icon.textContent = desired ? '♥' : '♡';
      label.textContent = desired ? '좋아요 취소' : '좋아요';
      status.textContent = message;
      form.setAttribute('aria-busy', String(inFlight || desired !== saved));
    }

    function removeUnlikedCard() {
      const list = form.closest('[data-liked-only]');
      if (!list) return;
      form.closest('[data-book-card]').remove();
      ['[data-book-count]', '[data-result-count]'].forEach((selector) => {
        const count = document.querySelector(selector);
        if (count) count.textContent = String(Math.max(0, Number(count.textContent) - 1));
      });
      if (!list.querySelector('[data-book-card]')) {
        const empty = document.querySelector('#liked-empty-template');
        list.append(empty.content.cloneNode(true));
      }
    }

    async function save() {
      if (inFlight || !ready) return;
      if (desired === saved) {
        paint();
        return;
      }
      const requested = desired;
      const body = new URLSearchParams({ liked: String(requested) });
      inFlight = true;
      ready = false;
      paint('저장 중…');
      try {
        const response = await fetch(form.action, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Accept': 'application/json',
            'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
          },
          body,
        });
        if (response.status === 401 || response.redirected) {
          throw new Error('로그인이 만료되었습니다. 새로고침 후 로그인해 주세요.');
        }
        if (!response.ok) throw new Error('저장하지 못했습니다. 다시 눌러 주세요.');
        const data = await response.json();
        if (typeof data.liked !== 'boolean') throw new Error('응답을 확인하지 못했습니다. 다시 눌러 주세요.');
        saved = data.liked;
        inFlight = false;
        if (desired === saved) {
          paint('저장되었습니다.');
          if (!saved) removeUnlikedCard();
        } else {
          paint('변경 대기 중…');
          if (ready) save();
        }
      } catch (error) {
        inFlight = false;
        ready = false;
        clearTimeout(timer);
        desired = saved;
        paint(error.message || '저장하지 못했습니다. 다시 눌러 주세요.');
      }
    }

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      desired = !desired;
      ready = false;
      paint('변경 대기 중…');
      clearTimeout(timer);
      timer = setTimeout(() => {
        ready = true;
        save();
      }, DEBOUNCE_MS);
    });
  });
})();
