const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../../static/js/book-likes.js'), 'utf8');

function setup({ liked = false, filtered = false } = {}) {
  let now = 0;
  let sequence = 0;
  const timers = new Map();
  const requests = [];
  const attributes = new Map([['aria-pressed', String(liked)]]);
  const button = { getAttribute: (key) => attributes.get(key), setAttribute: (key, value) => attributes.set(key, value), classList: { toggle() {} } };
  const icon = {};
  const label = {};
  const status = {};
  const count = { textContent: '1' };
  const card = { removed: false, remove() { this.removed = true; } };
  const list = { emptyAdded: false, querySelector: () => card.removed ? null : card, append() { this.emptyAdded = true; } };
  let submit;
  const form = {
    action: '/books/1/like/',
    querySelector(selector) {
      return { button, '[data-like-icon]': icon, '[data-like-label]': label, '[data-like-status]': status, '[name="csrfmiddlewaretoken"]': { value: 'csrf-token' } }[selector];
    },
    setAttribute() {},
    addEventListener(name, handler) { assert.equal(name, 'submit'); submit = handler; },
    closest(selector) { return selector === '[data-book-card]' ? card : filtered ? list : null; },
  };
  vm.runInNewContext(source, {
    document: {
      querySelectorAll: () => [form],
      querySelector: (selector) => selector === '[data-book-count]' ? count : selector === '#liked-empty-template' ? { content: { cloneNode: () => ({}) } } : null,
    },
    URLSearchParams,
    setTimeout(callback, delay) { const id = ++sequence; timers.set(id, { callback, due: now + delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) { return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject })); },
  });
  return {
    requests, attributes, status, card, list, count,
    click() { submit({ preventDefault() {} }); },
    advance(ms) {
      now += ms;
      for (const [id, timer] of timers) {
        if (timer.due <= now) { timers.delete(id); timer.callback(); }
      }
    },
    async reply(index, liked, response = {}) {
      requests[index].resolve({ ok: true, status: 200, json: async () => ({ liked }), ...response });
      await new Promise(setImmediate);
    },
  };
}

test('waits 300ms after the final click and submits only the final state', async () => {
  const app = setup();
  app.click(); app.advance(200); app.click(); app.advance(200); app.click();
  app.advance(299);
  assert.equal(app.requests.length, 0);
  app.advance(1);
  assert.equal(app.requests.length, 1);
  const { url, options } = app.requests[0];
  assert.equal(url, '/books/1/like/');
  assert.equal(options.method, 'POST');
  assert.equal(options.headers['X-CSRFToken'], 'csrf-token');
  assert.equal(options.body.get('liked'), 'true');
  await app.reply(0, true);
  assert.equal(app.attributes.get('aria-pressed'), 'true');
});

test('an even number of rapid clicks does not send an unchanged state', () => {
  const app = setup();
  app.click(); app.click(); app.advance(300);
  assert.equal(app.requests.length, 0);
  assert.equal(app.attributes.get('aria-pressed'), 'false');
});

test('serializes slow requests and saves the final intent after the first request', async () => {
  const app = setup();
  app.click(); app.advance(300);
  app.click(); app.advance(300);
  assert.equal(app.requests.length, 1);
  await app.reply(0, true);
  assert.equal(app.requests.length, 2);
  assert.equal(app.requests[1].options.body.get('liked'), 'false');
  await app.reply(1, false);
  assert.equal(app.attributes.get('aria-pressed'), 'false');
});

test('a slow response does not skip the debounce of a newer click', async () => {
  const app = setup();
  app.click(); app.advance(300); app.click();
  await app.reply(0, true);
  assert.equal(app.requests.length, 1);
  app.advance(299);
  assert.equal(app.requests.length, 1);
  app.advance(1);
  assert.equal(app.requests.length, 2);
  await app.reply(1, false);
});

test('failed requests roll back UI and allow another attempt', async () => {
  const app = setup();
  app.click(); app.advance(300);
  app.requests[0].reject(new Error('연결 실패'));
  await new Promise(setImmediate);
  assert.equal(app.attributes.get('aria-pressed'), 'false');
  assert.equal(app.status.textContent, '연결 실패');
  app.click(); app.advance(300);
  assert.equal(app.requests.length, 2);
  await app.reply(1, true);
});

test('expired sessions show a login message and restore the saved state', async () => {
  const app = setup();
  app.click(); app.advance(300);
  await app.reply(0, false, { ok: false, status: 401 });
  assert.equal(app.attributes.get('aria-pressed'), 'false');
  assert.match(app.status.textContent, /로그인/);
});

test('removes an unliked card and updates the empty filtered list after saving', async () => {
  const app = setup({ liked: true, filtered: true });
  app.click(); app.advance(300);
  assert.equal(app.card.removed, false);
  await app.reply(0, false);
  assert.equal(app.card.removed, true);
  assert.equal(app.count.textContent, '0');
  assert.equal(app.list.emptyAdded, true);
});
