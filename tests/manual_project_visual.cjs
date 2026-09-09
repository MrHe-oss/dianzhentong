const {chromium}=require('playwright');
const os=require('os');const path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try {
  for(const width of [1280,390]) {
   const page=await browser.newPage({viewport:{width,height:900}});
   await page.goto(process.env.LAB_URL || 'http://localhost:8517');
   await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
   const chapter=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
   await chapter.click();await chapter.fill('简单PLC项目流程');
   await page.getByRole('option').filter({hasText:'简单PLC项目流程'}).click();
   await page.getByRole('button',{name:'开始互动识图',exact:true}).click();
   for(const [prompt,answer] of [['首先应回到哪个环节？','需求与控制目标'],['定义清楚后应完成什么检查？','工程一致性与编译检查'],['编译通过后还需要什么？','离线模拟逻辑复盘']]) {
    await page.getByRole('heading',{name:prompt,exact:true}).waitFor();
    const radios=page.getByTestId('stRadio');
    await radios.getByText('不确定',{exact:true}).click();
    await page.getByRole('button',{name:'提交本步判断',exact:true}).click();
    await page.getByText('你的首次判断：不确定（后续更正不改变首次得分）',{exact:true}).waitFor();
    await radios.getByText(answer,{exact:true}).click();
    await page.getByRole('button',{name:'提交本步判断',exact:true}).click();
    await page.getByRole('button',{name:'进入下一步',exact:true}).click();
   }
   await page.getByText('0 / 3（0%）',{exact:true}).waitFor();
   await page.getByRole('button',{name:'返回本教材单元',exact:true}).scrollIntoViewIfNeeded();
   if(await page.getByTestId('stException').count()) throw Error('Exception');
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Overflow');
   const image=path.join(os.tmpdir(),`dzt-v414-project-${width}.png`);
   await page.screenshot({path:image});
   await page.getByRole('button',{name:'返回本教材单元',exact:true}).click();
   await page.getByRole('button',{name:'启动、保持与停止优先',exact:true}).waitFor();
   console.log(JSON.stringify({width,image,firstAnswers:true,returned:true,holdEntry:true}));
   await page.close();
  }
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
