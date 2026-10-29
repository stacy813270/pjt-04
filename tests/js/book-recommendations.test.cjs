const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../../static/js/book-recommendations.js'), 'utf8');
const recommended = () => ({ title: '끝없는 이야기', author: '미하엘 엔데', category: '소설', description: '소개', reason: '추천 이유', detail_url: '/books/3/' });

function setup({ disabled = false } = {}) {
  let now = 1000;
  let sequence = 0;
  let submit;
  const requests = [];
  const timers = new Map();
  const intervals = [];
  const button = { disabled, textContent: '추천받기' };
  const status = { textContent: '', classList: { toggle() {} } };
  const results = { hidden: true };
  const list = { cards: [], replaceChildren() { this.cards = []; }, append(card) { this.cards.push(card); } };
  const template = { content: { cloneNode() {
    const fields = {};
    return { fields, querySelector(selector) {
      return fields[selector] ||= { textContent: '', hidden: true };
    } };
  } } };
  const form = {
    action: '/books/recommendations/', dataset: { throttleSeconds: '30' },
    querySelector(selector) { return selector === 'button' ? button : { value: 'csrf-token' }; },
    addEventListener(event, handler) { assert.equal(event, 'submit'); submit = handler; },
    setAttribute() {},
  };
  const elements = {
    '[data-recommendation-form]': form, '[data-recommendation-status]': status,
    '[data-recommendation-results]': results, '[data-recommendation-list]': list,
    '#recommendation-card-template': template,
  };
  vm.runInNewContext(source, {
    document: { querySelector: (selector) => elements[selector] },
    Date: { now: () => now }, AbortController,
    setInterval(callback) { intervals.push(callback); },
    setTimeout(callback, delay) { const id = ++sequence; timers.set(id, { callback, due: now + delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) {
      return new Promise((resolve, reject) => {
        options.signal.addEventListener('abort', () => reject(Object.assign(new Error('timeout'), { name: 'AbortError' })));
        requests.push({ url, options, resolve, reject });
      });
    },
  });
  return {
    requests, button, status, results, list,
    click() { return submit({ preventDefault() {} }); },
    advance(ms) {
      now += ms;
      for (const [id, timer] of timers) {
        if (timer.due <= now) { timers.delete(id); timer.callback(); }
      }
      intervals.forEach((callback) => callback());
    },
    async reply(index, { status = 200, data, retryAfter } = {}) {
      requests[index].resolve({
        ok: status >= 200 && status < 300, status, redirected: false,
        headers: { get: () => retryAfter ? String(retryAfter) : null },
        json: async () => data || { recommendations: [recommended()], liked_count: 2 },
      });
      await new Promise(setImmediate);
    },
  };
}

test('starts immediately and ignores rapid clicks without trailing requests', async () => {
  const app = setup();
  const pending = app.click();
  assert.equal(app.requests.length, 1);
  await app.click(); await app.click();
  assert.equal(app.requests.length, 1);
  assert.equal(app.requests[0].options.method, 'POST');
  assert.equal(app.requests[0].options.headers['X-CSRFToken'], 'csrf-token');
  await app.reply(0);
  await pending;
  app.advance(29999);
  await app.click();
  assert.equal(app.requests.length, 1);
  app.advance(1);
  assert.equal(app.button.disabled, false);
  assert.equal(app.requests.length, 1);
  const second = app.click();
  assert.equal(app.requests.length, 2);
  await app.reply(1); await second;
});

test('keeps the button disabled while a slow request is still running', async () => {
  const app = setup();
  const pending = app.click();
  app.advance(31000);
  assert.equal(app.button.disabled, true);
  await app.click();
  assert.equal(app.requests.length, 1);
  await app.reply(0); await pending;
  assert.equal(app.button.disabled, false);
});

test('renders all book fields as text and only trusted local detail links', async () => {
  const app = setup();
  const pending = app.click();
  const book = recommended();
  book.title = '<img src=x onerror=alert(1)>';
  await app.reply(0, { data: { recommendations: [book, { ...recommended(), detail_url: 'javascript:alert(1)' }], liked_count: 2 } });
  await pending;
  assert.equal(app.results.hidden, false);
  assert.equal(app.list.cards[0].fields['[data-recommended-title]'].textContent, book.title);
  assert.equal(app.list.cards[0].fields['[data-recommended-reason]'].textContent, book.reason);
  assert.equal(app.list.cards[0].fields['[data-recommended-link]'].href, '/books/3/');
  assert.equal(app.list.cards[0].fields['[data-recommended-link]'].hidden, false);
  assert.equal(app.list.cards[1].fields['[data-recommended-link]'], undefined);
});

test('honors a longer server Retry-After value', async () => {
  const app = setup();
  const pending = app.click();
  await app.reply(0, { status: 429, retryAfter: 45, data: { error: '잠시 기다려 주세요.' } });
  await pending;
  app.advance(30000);
  await app.click();
  assert.equal(app.requests.length, 1);
  assert.equal(app.results.hidden, true);
  assert.equal(app.status.textContent, '잠시 기다려 주세요.');
  app.advance(15000);
  assert.equal(app.button.disabled, false);
});

test('shows login and backend errors without rendering results', async () => {
  for (const [status, message] of [[401, '로그인'], [503, '서비스 준비 중']]) {
    const app = setup();
    const pending = app.click();
    await app.reply(0, { status, data: { error: message } }); await pending;
    assert.ok(app.status.textContent.includes(message));
    assert.equal(app.results.hidden, true);
  }
});

test('rejects malformed results and allows retry when throttle expires', async () => {
  const app = setup();
  const pending = app.click();
  await app.reply(0, { data: { recommendations: [], liked_count: 1 } }); await pending;
  assert.equal(app.results.hidden, true);
  assert.ok(app.status.textContent.includes('올바르지'));
  app.advance(30000);
  const retry = app.click();
  await app.reply(1); await retry;
  assert.equal(app.results.hidden, false);
});

test('times out a request and restores the button without queuing another request', async () => {
  const app = setup();
  const pending = app.click();
  app.advance(75000);
  await pending;
  assert.equal(app.requests.length, 1);
  assert.equal(app.button.disabled, false);
  assert.ok(app.status.textContent.includes('시간이 초과'));
});

test('does not submit when the page has no liked books', async () => {
  const app = setup({ disabled: true });
  await app.click(); app.advance(60000);
  assert.equal(app.requests.length, 0);
  assert.equal(app.button.disabled, true);
});
