const {chromium}=require('playwright');
const os=require('os');
const path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try {
  for(const width of [1280,390]) {
   const page=await browser.newPage({viewport:{width,height:900}});
   await page.goto(process.env.LAB_URL || 'http://localhost:8515');
   await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
   const chapter=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
   await chapter.click();await chapter.fill('TIA博途软件基础');
   await page.getByRole('option').filter({hasText:'TIA博途软件基础'}).click();
   await page.getByRole('button',{name:'工程对象归类练习',exact:true}).click();
   await page.getByText('当前对象 · 工程项目',{exact:true}).waitFor();
   const image=path.join(os.tmpdir(),`dzt-v413-tia-${width}.png`);
   await page.screenshot({path:image,fullPage:true});
   for(const answer of ['工程项目','设备组态','程序块']) {
    await page.getByText(`当前对象 · ${answer}`,{exact:true}).waitFor();
    const radios=page.getByTestId('stRadio');
    await radios.getByText('不确定',{exact:true}).click();
    await page.getByRole('button',{name:'提交本步判断',exact:true}).click();
    await page.getByText('你的首次判断：不确定（后续更正不改变首次得分）',{exact:true}).waitFor();
    await radios.getByText(answer,{exact:true}).click();
    await page.getByRole('button',{name:'提交本步判断',exact:true}).click();
    await page.getByRole('button',{name:'进入下一步',exact:true}).click();
   }
   await page.getByText('0 / 3（0%）',{exact:true}).waitFor();
   if(await page.getByTestId('stException').count()) throw Error('Exception');
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Overflow');
   await page.getByRole('button',{name:'返回本教材单元',exact:true}).click();
   await page.getByRole('button',{name:'工程对象归类练习',exact:true}).waitFor();
   console.log(JSON.stringify({width,image,firstAnswers:true,returned:true}));
   await page.close();
  }
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
