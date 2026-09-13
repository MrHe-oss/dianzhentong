// Read-only deployed-version/entry check; can also target a local smoke server.
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage();
 try {
  await page.goto(process.env.LAB_URL || 'https://dianzhentong.streamlit.app', {waitUntil:'domcontentloaded',timeout:45000});
  await page.getByRole('button',{name:'进入教材学习',exact:true}).waitFor({timeout:45000});
  if(!(await page.locator('body').innerText()).includes('4.18')) throw Error('Expected v4.18');
  await page.getByRole('button',{name:'进入教材学习',exact:true}).click();
  const chapter=page.getByTestId('stSelectbox').filter({hasText:'选择章节'}).getByRole('combobox');
  await chapter.click(); await chapter.fill('PLC点动与长动的逻辑学习');
  await page.getByRole('option').filter({hasText:'PLC点动与长动的逻辑学习'}).click();
  await page.getByText(/题库总量 8 题 · 可用于独立测验 7 题/).waitFor();
  await page.getByRole('heading',{name:'对比互动：点动与长动',exact:true}).waitFor();
  if(await page.getByTestId('stException').count()) throw Error('Application exception');
  console.log(JSON.stringify({url:page.url(),version:'4.18',unit:true,pool:7}));
 } catch(error) {
  console.error(JSON.stringify({url:page.url(),error:String(error),visibleText:(await page.locator('body').innerText().catch(()=>'' )).slice(0,1800)}));
  process.exitCode=1;
 } finally {await browser.close();}
})();
