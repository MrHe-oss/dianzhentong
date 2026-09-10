const {chromium}=require('playwright');
const os=require('os');const path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const width of [1280,390]){
   const page=await browser.newPage({viewport:{width,height:900}});
   await page.goto(process.env.LAB_URL || 'http://localhost:8520');
   await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
   const selector=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
   await selector.click();await selector.fill('PLC正反转控制的逻辑学习');
   await page.getByRole('option').filter({hasText:'PLC正反转控制的逻辑学习'}).click();
   await page.getByRole('heading',{name:'互动观察：方向请求与保持状态',exact:true}).waitFor();
   for(const [forward,reverse,stop,expected] of [[true,false,false,'正向'],[false,false,false,'正向'],[false,true,false,'正向'],[false,true,true,'停止'],[false,true,false,'反向'],[true,true,false,'停止']]){
    for(const [label,value] of [['正向请求',forward],['反向请求',reverse],['停止请求',stop]]){
     const input=page.getByRole('checkbox',{name:label,exact:true});
     if(await input.isChecked()!==value){
      await page.getByTestId('stCheckbox').getByText(label,{exact:true}).click();
      await page.waitForTimeout(400);
     }
    }
    await page.getByRole('button',{name:'计算下一步',exact:true}).click();
    await page.getByText('当前教学状态：'+expected,{exact:true}).waitFor();
    await page.waitForTimeout(400);
   }
   await page.getByRole('heading',{name:'互动观察：方向请求与保持状态',exact:true}).scrollIntoViewIfNeeded();
   const check=async(name)=>{
    if(await page.getByTestId('stException').count())throw Error('App exception');
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow');
    await page.screenshot({path:path.join(os.tmpdir(),`dzt-v417-${name}-${width}.png`)});
   };
   await check('logic');
   const solve=async(n)=>{
    for(let i=1;i<=n;i++){
     await page.getByText(`第 ${i} / ${n} 题`,{exact:true}).waitFor();
     await page.getByTestId('stRadio').getByText('不确定',{exact:true}).click();
     await page.getByRole('button',{name:'提交答案',exact:true}).click();
     await page.getByText('你的首次判断： 不确定',{exact:true}).waitFor();
     if(i===1){
      await page.getByRole('button',{name:'回看本题知识点',exact:true}).click();
      await page.getByRole('button',{name:'返回原练习',exact:true}).click();
     }
     await page.getByRole('button',{name:i===n?'查看成绩':'下一题',exact:true}).click();
    }
   };
   if(await page.getByRole('button',{name:'开始学前小测',exact:true}).count()){
    await page.getByRole('button',{name:'开始学前小测',exact:true}).click();
    await solve(3);
    await page.getByRole('button',{name:'返回教材单元',exact:true}).click();
   }
   await page.getByRole('button',{name:'开始学后评测',exact:true}).click();
   await solve(5);
   await page.getByText('0 / 5（0%）',{exact:true}).waitFor();
   await page.getByRole('button',{name:'返回教材单元',exact:true}).scrollIntoViewIfNeeded();
   await check('report');
   await page.getByRole('button',{name:'复习知识卡',exact:true}).first().click();
   await page.getByRole('button',{name:'返回原练习报告',exact:true}).click();
   await page.getByText('0 / 5（0%）',{exact:true}).waitFor();
   console.log(JSON.stringify({width,stateTransitions:true,quiz:true,relearn:true}));
   await page.close();
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
