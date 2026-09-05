// Optional desktop/mobile smoke test; NODE_PATH must expose Playwright.
const { chromium } = require('playwright');
const path = require('path');
const os = require('os');
(async () => {
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  try {
    for (const width of [1280, 390]) {
      const page = await browser.newPage({viewport: {width, height: 900}});
      await page.goto(process.env.LAB_URL || 'http://localhost:8515');
      const route = page.getByTestId('stSelectbox').filter({hasText: '选择学习路线'}).getByRole('combobox');
      await route.click();
      await page.getByRole('option').filter({hasText: '电路基础入门'}).click();
      await page.getByRole('button', {name: '进入教材学习', exact: true}).click();
      await page.getByText('互动观察：欧姆定律与功率', {exact: true}).click();
      await page.getByRole('button', {name: '保存当前值作为对比起点', exact: true}).click();
      const voltage = page.getByRole('slider').first();
      await voltage.focus();
      for (let i=0; i<4; i++) await voltage.press('ArrowRight');
      await page.getByText(/电流是 2 倍，功率是 4 倍/).waitFor();
      await page.getByRole('button', {name: '保存当前值作为对比起点', exact: true}).scrollIntoViewIfNeeded();
      if (await page.getByTestId('stException').count()) throw Error('Streamlit exception');
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow) throw Error(`Horizontal overflow at ${width}`);
      const image = path.join(os.tmpdir(), `dzt-v48-${width}.png`);
      await page.screenshot({path: image});
      console.log(JSON.stringify({width, overflow, scalingVerified: true, image}));
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1)});
