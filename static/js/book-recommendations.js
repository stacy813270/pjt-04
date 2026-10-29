(() => {
  'use strict';

  const form = document.querySelector('[data-recommendation-form]');
  if (!form) return;
  const button = form.querySelector('button');
  const status = document.querySelector('[data-recommendation-status]');
  const results = document.querySelector('[data-recommendation-results]');
  const list = document.querySelector('[data-recommendation-list]');
  const template = document.querySelector('#recommendation-card-template');
  const interval = Number(form.dataset.throttleSeconds) * 1000;
  const initiallyDisabled = button.disabled;
  let nextAllowedAt = 0;
  let inFlight = false;

  function updateButton() {
    const seconds = Math.max(0, Math.ceil((nextAllowedAt - Date.now()) / 1000));
    button.disabled = initiallyDisabled || inFlight || seconds > 0;
    button.textContent = inFlight ? '추천받는 중…' : seconds > 0 ? `${seconds}초 후 다시 추천` : '추천받기';
    form.setAttribute('aria-busy', String(inFlight));
  }

  function showStatus(message, isError = false) {
    status.textContent = message;
    status.classList.toggle('is-error', isError);
  }

  function renderBooks(books) {
    list.replaceChildren();
    for (const book of books) {
      const card = template.content.cloneNode(true);
      for (const field of ['title', 'author', 'category', 'description', 'reason']) {
        if (typeof book[field] !== 'string') throw new Error('추천 결과의 형식이 올바르지 않습니다.');
        card.querySelector(`[data-recommended-${field}]`).textContent = book[field];
      }
      if (typeof book.detail_url === 'string' && /^\/books\/\d+\/$/.test(book.detail_url)) {
        const link = card.querySelector('[data-recommended-link]');
        link.href = book.detail_url;
        link.hidden = false;
      }
      list.append(card);
    }
    results.hidden = false;
  }

  // Leading-edge throttle: start immediately; ignored clicks never schedule another request.
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (initiallyDisabled || inFlight || Date.now() < nextAllowedAt) return;
    inFlight = true;
    nextAllowedAt = Date.now() + interval;
    results.hidden = true;
    updateButton();
    showStatus('좋아요한 책을 살펴보고 추천을 준비하고 있어요.');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 75000);
    try {
      const response = await fetch(form.action, {
        method: 'POST', credentials: 'same-origin',
        headers: {
          'Accept': 'application/json',
          'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
        },
        signal: controller.signal,
      });
      if (response.status === 401 || response.redirected) {
        throw new Error('로그인이 만료되었습니다. 새로고침 후 로그인해 주세요.');
      }
      const data = await response.json();
      if (response.status === 429) {
        const retryAfter = Number(response.headers.get('Retry-After') || data.retry_after);
        if (Number.isFinite(retryAfter) && retryAfter > 0) {
          nextAllowedAt = Math.max(nextAllowedAt, Date.now() + retryAfter * 1000);
        }
      }
      if (!response.ok) throw new Error(data.error || '추천을 받지 못했습니다. 잠시 후 다시 시도해 주세요.');
      if (!Array.isArray(data.recommendations) || !data.recommendations.length || data.recommendations.length > 3) {
        throw new Error('추천 도서 목록이 올바르지 않습니다. 잠시 후 다시 시도해 주세요.');
      }
      renderBooks(data.recommendations);
      showStatus(`좋아요한 ${data.liked_count}권을 바탕으로 ${data.recommendations.length}권을 추천했어요.`);
    } catch (error) {
      showStatus(error.name === 'AbortError'
        ? '추천 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.'
        : error instanceof TypeError || error instanceof SyntaxError
          ? '추천 서비스에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.'
          : error.message || '추천을 받지 못했습니다. 잠시 후 다시 시도해 주세요.', true);
    } finally {
      clearTimeout(timeout);
      inFlight = false;
      updateButton();
    }
  });

  setInterval(updateButton, 1000);
})();
