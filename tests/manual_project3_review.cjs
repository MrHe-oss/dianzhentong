const {chromium}=require('playwright');
const os=require('os'),path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [1280,390]){
   const page=await browser.newPage({viewport:{width,height:900}});
   await page.goto(process.env.LAB_URL || 'http://localhost:8523');
   await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
   const selector=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
   await selector.click(); await selector.fill('PLC星—三角启动的逻辑学习');
   await page.getByRole('option').filter({hasText:'PLC星—三角启动的逻辑学习'}).click();
   await page.getByRole('button',{name:'项目3学习小结与综合复习',exact:true}).click();
   await page.getByRole('heading',{name:'四种教学逻辑的区别',exact:true}).waitFor();
   await page.getByText('查看提示',{exact:true}).first().click();
   await page.getByText('展开答案与推理',{exact:true}).first().click();
   await page.getByText('本轮Y=假。先算A或B，再与非T组合；不是自动保持。',{exact:true}).waitFor();
   await page.waitForTimeout(400);
   const check=async(name)=>{
    if(await page.getByTestId('stException').count())throw Error('Application exception');
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow');
    await page.screenshot({path:path.join(os.tmpdir(),`dzt-v420-${name}-${width}.png`)});
   };
   await check('summary');
   await page.getByRole('button',{name:'开始项目3综合测验',exact:true}).click();
   for(let i=1;i<=8;i++){
    await page.getByText(`第 ${i} / 8 题`,{exact:true}).waitFor();
    await page.getByTestId('stRadio').getByText('不确定',{exact:true}).click();
    await page.getByRole('button',{name:'提交答案',exact:true}).click();
    await page.getByText('你的首次判断： 不确定',{exact:true}).waitFor();
    if(i===1){
     await page.getByRole('button',{name:'回看本题知识点',exact:true}).click();
     await page.getByRole('button',{name:'返回原练习',exact:true}).click();
    }
    await page.getByRole('button',{name:i===8?'查看成绩':'下一题',exact:true}).click();
   }
   await page.getByText('0 / 8（0%）',{exact:true}).waitFor();
   const download=page.waitForEvent('download');
   await page.getByRole('button',{name:'下载项目学习报告',exact:true}).click();
   const file=await download;
   if(!file.suggestedFilename().includes('项目3'))throw Error('Wrong download');
   await page.getByRole('heading',{name:'📋 项目3综合学习报告',exact:true}).scrollIntoViewIfNeeded();
   await check('report');
   await page.getByRole('button',{name:'返回项目3复习',exact:true}).click();
   await page.getByRole('button',{name:'查看最近综合报告',exact:true}).click();
   await page.getByRole('button',{name:'复习知识卡',exact:true}).first().click();
   await page.getByRole('button',{name:'返回原练习报告',exact:true}).click();
   await page.getByText('0 / 8（0%）',{exact:true}).waitFor();
   console.log(JSON.stringify({width,summary:true,quiz:true,download:true,historyRelearn:true}));
   await page.close();
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
