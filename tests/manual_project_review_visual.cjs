const {chromium}=require('playwright');
const os=require('os');const path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try {
  for(const width of [1280,390]) {
   const page=await browser.newPage({viewport:{width,height:900}});
   await page.goto(process.env.LAB_URL || 'http://localhost:8518');
   await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
   const chapter=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
   await chapter.click();await chapter.fill('PLC程序设计基础');
   await page.getByRole('option').filter({hasText:'PLC程序设计基础'}).click();
   await page.getByRole('button',{name:'项目2学习概览与综合复习',exact:true}).click();
   await page.getByRole('button',{name:'开始项目2综合测验',exact:true}).waitFor();
   const check=async(label)=>{
    if(await page.getByTestId('stException').count()) throw Error('Exception '+label);
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Overflow '+label);
    await page.screenshot({path:path.join(os.tmpdir(),`dzt-v415-${label}-${width}.png`)});
   };
   await check('overview');
   await page.getByRole('button',{name:'开始项目2综合测验',exact:true}).click();
   for(let i=1;i<=8;i++) {
    await page.getByText(`第 ${i} / 8 题`,{exact:true}).waitFor();
    await page.getByTestId('stRadio').getByText('不确定',{exact:true}).click();
    await page.getByRole('button',{name:'提交答案',exact:true}).click();
    await page.getByText('你的首次判断： 不确定',{exact:true}).waitFor();
    if(i===5){
     await page.getByRole('button',{name:'回看本题知识点',exact:true}).click();
     await page.getByRole('button',{name:/返回原/}).click();
     await page.getByText(`第 ${i} / 8 题`,{exact:true}).waitFor();
    }
    await page.getByRole('button',{name:i===8?'查看成绩':'下一题',exact:true}).click();
   }
   await page.getByText('0 / 8（0%）',{exact:true}).waitFor();
   await page.getByRole('button',{name:'返回项目2学习概览',exact:true}).scrollIntoViewIfNeeded();
   await check('report');
   const downloadPromise=page.waitForEvent('download');
   await page.getByRole('button',{name:'下载项目学习报告',exact:true}).click();
   const download=await downloadPromise;
   if(!download.suggestedFilename().endsWith('.txt'))throw Error('Download');
   await page.getByRole('button',{name:'返回项目2学习概览',exact:true}).click();
   await page.getByRole('button',{name:'查看最近综合报告',exact:true}).click();
   await page.getByText('0 / 8（0%）',{exact:true}).waitFor();
   await check('restored-report');
   console.log(JSON.stringify({width,complete:true,download:true,restored:true}));
   await page.close();
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
