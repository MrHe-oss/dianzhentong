// Optional desktop/mobile regression for textbook question -> lesson -> question.
const {chromium} = require('playwright');
const os = require('os');
const path = require('path');
(async()=>{
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try {
    for (const width of [1280,390]) {
      const page=await browser.newPage({viewport:{width,height:900}});
      await page.goto(process.env.LAB_URL || 'http://localhost:8515');
      await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
      const selector=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
      await selector.click();await selector.fill('硬件');
      await page.getByRole('option').filter({hasText:'硬件'}).click();
      await page.getByRole('button',{name:'开始学前小测',exact:true}).click();
      await page.getByText('不确定',{exact:true}).click();
      await page.getByRole('button',{name:'提交答案',exact:true}).click();
      await page.getByRole('button',{name:'回看本题知识点',exact:true}).click();
      await page.getByRole('button',{name:'返回原练习',exact:true}).click();
      await page.getByText('你的首次判断：').waitFor();
      await page.getByRole('button',{name:'下一题',exact:true}).scrollIntoViewIfNeeded();
      if(await page.getByTestId('stException').count()) throw Error('Streamlit exception');
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Horizontal overflow');
      const image=path.join(os.tmpdir(),`dzt-v411-return-${width}.png`);
      await page.screenshot({path:image});
      await page.getByRole('button',{name:'下一题',exact:true}).click();
      await page.getByRole('button',{name:'提交答案',exact:true}).waitFor();
      console.log(JSON.stringify({width,returned:true,nextQuestion:true,image}));
      await page.close();
    }
  } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
