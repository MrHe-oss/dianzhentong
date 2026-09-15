const {chromium}=require('playwright');
const os=require('os'),path=require('path');
(async()=>{
 const b=await chromium.launch({channel:'msedge',headless:true});
 try{for(const width of [1280,390]){
  const p=await b.newPage({viewport:{width,height:900}});
  await p.goto(process.env.LAB_URL || 'http://localhost:8526');
  await p.getByRole('button',{name:'进入教材学习',exact:true}).click();
  const selector=p.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
  await selector.click();await selector.fill('移动指令与数据传递基础');
  await p.getByRole('option').filter({hasText:'移动指令与数据传递基础'}).click();
  const execute=()=>p.getByRole('button',{name:'执行一次',exact:true}).click();
  await execute();await p.getByText('目标B：3 → 12',{exact:true}).waitFor();
  const input=p.getByRole('spinbutton',{name:'源A的当前值',exact:true});
  await input.fill('9');await input.press('Tab');
  await p.getByTestId('stCheckbox').getByText('执行条件',{exact:true}).click();
  await execute();await p.getByText('目标B：12 → 12',{exact:true}).waitFor();
  await p.getByTestId('stCheckbox').getByText('执行条件',{exact:true}).click();
  await execute();await p.getByText('目标B：12 → 9',{exact:true}).waitFor();
  const check=async(name)=>{
   if(await p.getByTestId('stException').count())throw Error('Application exception');
   if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow');
   await p.screenshot({path:path.join(os.tmpdir(),`dzt-v422-${name}-${width}.png`)});
  };
  await p.getByRole('heading',{name:'条件互动：单次数据复制',exact:true}).scrollIntoViewIfNeeded();await check('copy');
  const solve=async(n)=>{for(let i=1;i<=n;i++){
   await p.getByText(`第 ${i} / ${n} 题`,{exact:true}).waitFor();
   await p.getByTestId('stRadio').getByText('不确定',{exact:true}).click();
   await p.getByRole('button',{name:'提交答案',exact:true}).click();
   await p.getByText('你的首次判断： 不确定',{exact:true}).waitFor();
   if(i==1){await p.getByRole('button',{name:'回看本题知识点',exact:true}).click();await p.getByRole('button',{name:'返回原练习',exact:true}).click();}
   await p.getByRole('button',{name:i===n?'查看成绩':'下一题',exact:true}).click();
  }};
  if(await p.getByRole('button',{name:'开始学前小测',exact:true}).count()){
   await p.getByRole('button',{name:'开始学前小测',exact:true}).click();await solve(3);
   await p.getByRole('button',{name:'返回教材单元',exact:true}).click();
  }
  await p.getByRole('button',{name:'开始学后评测',exact:true}).click();await solve(5);
  await p.getByText('0 / 5（0%）',{exact:true}).waitFor();await check('report');
  await p.getByRole('button',{name:'复习知识卡',exact:true}).first().click();
  await p.getByRole('button',{name:'返回原练习报告',exact:true}).click();
  await p.getByRole('button',{name:'返回教材单元',exact:true}).click();
  await p.getByRole('heading',{name:'条件互动：单次数据复制',exact:true}).waitFor();
  console.log(JSON.stringify({width,copy:true,quiz:true,relearn:true}));await p.close();
 }}finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
