// Real-browser textbook example check; NODE_PATH must expose Playwright.
const {chromium} = require('playwright');
const path = require('path');
const os = require('os');
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    for (const width of [1280,390]) {
      const page = await browser.newPage({viewport:{width,height:900}});
      await page.goto(process.env.LAB_URL || 'http://localhost:8515');
      await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
      const chapter = page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
      await chapter.click();
      await chapter.fill('硬件');
      await page.getByRole('option').filter({hasText:'硬件'}).click();
      await page.getByText('🧩 原创例题：硬件角色分类',{exact:true}).click();
      await page.getByText('给我一个思考提示',{exact:true}).click();
      await page.getByText('查看分步解析与答案',{exact:true}).click();
      await page.getByText('变式练习',{exact:true}).waitFor();
      await page.getByText('查看分步解析与答案',{exact:true}).scrollIntoViewIfNeeded();
      if(await page.getByTestId('stException').count()) throw Error('Streamlit exception');
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Horizontal overflow');
      const image = path.join(os.tmpdir(),`dzt-v410-example-${width}.png`);
      await page.screenshot({path:image});
      console.log(JSON.stringify({width,image,exampleRevealed:true}));
      await page.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
