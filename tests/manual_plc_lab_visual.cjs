// Optional real-browser smoke check. NODE_PATH must expose Playwright.
const { chromium } = require('playwright');
const path = require('path');
const os = require('os');
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    for (const width of [1280,390]) {
      const page = await browser.newPage({viewport:{width,height:900}});
      await page.goto(process.env.LAB_URL || 'http://localhost:8515');
      await page.getByRole('button',{name:'📚 教材中心',exact:true}).waitFor({state:'attached'});
      if (width < 640)
        await page.getByTestId('stExpandSidebarButton').click();
      await page.getByRole('button',{name:'📚 教材中心',exact:true}).click();
      if (width < 640) await page.getByRole('button',{name:'keyboard_double_arrow_left',exact:true}).click();
      const select = page.getByTestId('stSelectbox').filter({hasText:'选择章节'});
      await select.getByRole('combobox').click();
      await select.getByRole('combobox').fill('PLC程序');
      await page.getByRole('option').filter({hasText:'程序'}).first().click();
      await page.getByRole('button',{name:'与、或、非：输入怎样决定结果',exact:true}).click();
      await page.getByRole('button',{name:'先做预测',exact:true}).click();
      await page.getByText('不确定',{exact:true}).click();
      await page.getByRole('button',{name:'提交首次判断',exact:true}).click();
      await page.getByRole('button',{name:'计算并观察',exact:true}).click();
      await page.getByText(/AND：A=/).waitFor();
      if (await page.getByTestId('stException').count()) throw Error('Streamlit exception');
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow) throw Error(`Horizontal overflow at ${width}`);
      await page.locator('.plc-nodes').scrollIntoViewIfNeeded();
      const image = path.join(os.tmpdir(),`dzt-v46-${width}.png`);
      await page.screenshot({path:image,fullPage:true});
      console.log(JSON.stringify({width,overflow,image}));
      await page.getByRole('button',{name:'完成观察，做迁移题',exact:true}).click();
      await page.getByText('真',{exact:true}).click();
      await page.getByRole('button',{name:'提交首次判断',exact:true}).click();
      const download = page.waitForEvent('download');
      await page.getByRole('button',{name:'下载互动学习报告',exact:true}).click();
      await download;
      await page.getByRole('button',{name:'返回教材单元',exact:true}).click();
      await page.getByRole('button',{name:'与、或、非：输入怎样决定结果',exact:true}).waitFor();
      if (await page.getByTestId('stException').count()) throw Error('Report/return exception');
      console.log(JSON.stringify({width,reportDownload:true,returnedToUnit:true}));
      await page.getByRole('button',{name:'扫描过程：输入变化何时生效',exact:true}).click();
      await page.getByRole('button',{name:'先做预测',exact:true}).click();
      await page.getByText('假',{exact:true}).click();
      await page.getByRole('button',{name:'提交首次判断',exact:true}).click();
      await page.getByRole('button',{name:'读取输入快照',exact:true}).click();
      await page.getByText(/已完成：读取快照/).waitFor();
      await page.getByText('当前模拟输入为真',{exact:true}).click();
      await page.getByText('当前模拟输入：成立（真）；它不等于已读取的快照。',{exact:true}).waitFor();
      if (await page.locator('.plc-wait').count() !== 2) throw Error('Unexecuted stages must remain pending');
      await page.locator('.plc-nodes').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(os.tmpdir(),`dzt-v46-scan-${width}.png`)});
      await page.getByRole('button',{name:'执行本轮逻辑',exact:true}).click();
      await page.getByRole('button',{name:'更新显示结果',exact:true}).click();
      await page.getByText(/已完成：更新显示/).waitFor();
      if (await page.locator('.plc-wait').count()) throw Error('Updated cycle still pending');
      console.log(JSON.stringify({width,scanPending:true}));
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
