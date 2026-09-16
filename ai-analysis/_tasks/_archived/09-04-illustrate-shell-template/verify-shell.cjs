const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

function loadPlaywright() {
  try {
    return require('playwright');
  } catch (error) {
    const runtimeRoot = path.join(os.homedir(), '.cache/codex-runtimes');
    if (fs.existsSync(runtimeRoot)) {
      for (const runtime of fs.readdirSync(runtimeRoot)) {
        const candidate = path.join(runtimeRoot, runtime, 'dependencies/node/node_modules/playwright');
        if (fs.existsSync(candidate)) return require(candidate);
      }
    }
    throw new Error(`playwright is required; install it locally or expose it through NODE_PATH (${error.message})`);
  }
}

const { chromium } = loadPlaywright();

const repoRoot = path.resolve(__dirname, '../../../..');
const receiptDir = path.join(repoRoot, '.agent-tmp/air23-postbuild');
fs.mkdirSync(receiptDir, { recursive: true });

const server = http.createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  if (pathname.endsWith('/diagram-example.html')) {
    response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    response.end('<!doctype html><meta charset="utf-8"><title>stub</title><p>stub</p>');
    return;
  }
  const file = path.resolve(repoRoot, pathname.replace(/^\/+/, ''));
  if (!file.startsWith(`${repoRoot}${path.sep}`) || !fs.existsSync(file)) {
    response.writeHead(404).end('not found');
    return;
  }
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(fs.readFileSync(file));
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const cases = [
    {
      name: 'template',
      url: `${origin}/skills/_common/illustrate-report-shell.html`,
      first: 's2',
      valid: 's3',
      title: '{{REPORT_TITLE}}',
      text: '圖尚未產生',
    },
    {
      name: 'index',
      url: `${origin}/ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/index.html`,
      first: 's1',
      valid: 's4',
      title: 'AIR-23 illustrate 報告殼 template 化 — 任務簡報殼',
      text: '為什麼・動機鏈',
    },
  ];
  const browser = await chromium.launch({ headless: true });
  let passed = 0;
  const failures = [];
  const check = (condition, label, detail = '') => {
    if (condition) passed += 1;
    else failures.push(`${label}${detail ? `: ${detail}` : ''}`);
  };

  const templateFile = path.join(repoRoot, 'skills/_common/illustrate-report-shell.html');
  const indexFile = path.join(__dirname, 'index.html');
  const epFile = path.join(__dirname, 'ep.md');
  const cardFile = path.join(repoRoot, 'backlog/tasks/air-23 - illustrate-報告殼-template-化（可折疊-sidebar）.md');
  const templateHtml = fs.readFileSync(templateFile, 'utf8');
  const indexHtml = fs.readFileSync(indexFile, 'utf8');
  const epText = fs.readFileSync(epFile, 'utf8');
  const cardText = fs.readFileSync(cardFile, 'utf8');
  const requiredSlots = ['title', 'badge', 'meta', 'nav', 'section-content', 'diagram', 'backlinks', 'source'];
  check(!/SLOT:|\{\{[A-Z0-9_]+\}\}/.test(indexHtml), 'static: consumer placeholders absent');
  check(requiredSlots.every(slot => templateHtml.includes(`SLOT:${slot}`)), 'static: required template slots present');
  check(templateHtml.indexOf('<meta charset="UTF-8">') < templateHtml.indexOf('usage —'), 'static: charset precedes usage prose');
  const epDigest = crypto.createHash('sha256').update(epText).digest('hex').slice(0, 12);
  check(indexHtml.includes(`projection source：ep.md sha256:${epDigest}`), 'static: projection source matches EP content SHA', epDigest);
  const localLinks = [...epText.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)]
    .map(match => match[1].split('#')[0])
    .filter(target => target && !target.includes('://'));
  const missingLinks = localLinks.filter(target => !fs.existsSync(path.resolve(__dirname, target)));
  check(missingLinks.length === 0, 'static: EP local links resolve', missingLinks.join(', '));
  check(
    cardText.includes('/ai-rules/_tasks/_archived/09-04-illustrate-shell-template/index.html')
      && cardText.includes('ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/index.html'),
    'static: Done card points to final shell',
  );

  for (const item of cases) {
    const context = await browser.newContext({ viewport: { width: 1728, height: 900 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(item.url);
    await page.evaluate(() => localStorage.clear());
    await page.reload();

    check(await page.title() === item.title, `${item.name}: browser parse/title`, await page.title());
    check((await page.locator('body').textContent()).includes(item.text), `${item.name}: UTF-8 body text`);
    check(await page.locator('main section.active').getAttribute('id') === item.first, `${item.name}: default framed section`);
    const topology = await page.evaluate(() => ({
      nav: [...document.querySelectorAll('#sidebar li a')].map(a => a.hash.slice(1)),
      sections: [...document.querySelectorAll('main section')].map(s => s.id),
    }));
    check(JSON.stringify(topology.nav) === JSON.stringify(topology.sections), `${item.name}: nav/section topology`);

    const iframeBefore = await page.locator('iframe').count()
      ? await page.locator('iframe').first().evaluate(frame => {
          window.__air23FrameWindow = frame.contentWindow;
          return frame.src;
        })
      : null;
    await page.locator('#collapse-btn').click();
    await page.waitForTimeout(300);
    const collapsed = await page.evaluate(() => {
      const sidebar = document.getElementById('sidebar');
      const main = document.querySelector('main');
      const expand = document.getElementById('expand-btn');
      return {
        body: document.body.classList.contains('sidebar-collapsed'),
        sidebarWidth: sidebar.getBoundingClientRect().width,
        mainX: main.getBoundingClientRect().x,
        mainWidth: main.getBoundingClientRect().width,
        expandTop: expand.getBoundingClientRect().top,
        inert: sidebar.inert,
        ariaHidden: sidebar.getAttribute('aria-hidden'),
        focus: document.activeElement.id,
      };
    });
    check(collapsed.body && collapsed.sidebarWidth === 0 && collapsed.mainX === 0 && collapsed.mainWidth === 1728, `${item.name}: collapsed geometry`, JSON.stringify(collapsed));
    check(collapsed.expandTop === 20, `${item.name}: expand control top-left`, String(collapsed.expandTop));
    check(collapsed.inert && collapsed.ariaHidden === 'true' && collapsed.focus === 'expand-btn', `${item.name}: collapsed accessibility`, JSON.stringify(collapsed));
    check(await page.locator('#expand-btn').getAttribute('aria-expanded') === 'false', `${item.name}: collapsed aria-expanded`);
    check(await page.evaluate(() => localStorage.getItem('illustrate-shell-sidebar-collapsed')) === '1', `${item.name}: collapsed persistence write`);
    if (iframeBefore) {
      const iframeRetained = await page.locator('iframe').first().evaluate(
        (frame, source) => frame.src === source && frame.contentWindow === window.__air23FrameWindow,
        iframeBefore,
      );
      check(iframeRetained, `${item.name}: iframe retained`);
    }

    await page.reload();
    await page.waitForTimeout(300);
    const restored = await page.evaluate(() => ({
      body: document.body.classList.contains('sidebar-collapsed'),
      inert: document.getElementById('sidebar').inert,
      ariaHidden: document.getElementById('sidebar').getAttribute('aria-hidden'),
    }));
    check(restored.body && restored.inert && restored.ariaHidden === 'true', `${item.name}: collapsed state restored after reload`, JSON.stringify(restored));

    await page.locator('#expand-btn').click();
    await page.waitForTimeout(300);
    const expanded = await page.evaluate(() => ({
      body: document.body.classList.contains('sidebar-collapsed'),
      inert: document.getElementById('sidebar').inert,
      ariaHidden: document.getElementById('sidebar').hasAttribute('aria-hidden'),
      focus: document.activeElement.id,
    }));
    check(!expanded.body && !expanded.inert && !expanded.ariaHidden && expanded.focus === 'collapse-btn', `${item.name}: expanded accessibility`, JSON.stringify(expanded));

    await page.goto(`${item.url}?probe=existing-id#sidebar`);
    check(await page.locator('main section.active').getAttribute('id') === item.first, `${item.name}: hostile existing-id hash fallback`);
    await page.goto(`${item.url}?probe=unknown#does-not-exist`);
    check(await page.locator('main section.active').getAttribute('id') === item.first, `${item.name}: unknown hash fallback`);
    await page.goto(`${item.url}?probe=valid#${item.valid}`);
    check(await page.locator('main section.active').getAttribute('id') === item.valid, `${item.name}: valid hash restore`);

    await page.setViewportSize({ width: 1024, height: 768 });
    await page.locator('#collapse-btn').click();
    await page.waitForTimeout(300);
    const narrow = await page.evaluate(() => {
      const main = document.querySelector('main').getBoundingClientRect();
      const expand = document.getElementById('expand-btn').getBoundingClientRect();
      return { mainX: main.x, mainRight: main.right, expandRight: expand.right, scrollWidth: document.documentElement.scrollWidth };
    });
    check(narrow.mainX === 0 && narrow.mainRight === 1024 && narrow.expandRight > 0 && narrow.scrollWidth === 1024, `${item.name}: 1024px collapsed viewport`, JSON.stringify(narrow));
    await page.locator('#expand-btn').click();
    await page.setViewportSize({ width: 1728, height: 900 });

    await page.locator('#collapse-btn').click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(receiptDir, `${item.name}-collapsed-final.png`), fullPage: true });
    if (item.name === 'index') {
      await page.locator('#expand-btn').click();
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(receiptDir, 'index-expanded-s4-final.png'), fullPage: true });
    }
    check(errors.length === 0, `${item.name}: no page errors`, errors.join(' | '));
    await context.close();
  }

  await browser.close();
  server.close();
  console.log(JSON.stringify({ passed, failed: failures.length, failures }, null, 2));
  process.exit(failures.length ? 1 : 0);
})().catch(error => {
  server.close();
  console.error(error);
  process.exit(1);
});
