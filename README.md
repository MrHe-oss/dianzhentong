# 电诊通（Dianzhentong）

电诊通是面向电气工程及其自动化专业学生的电气知识与模拟实训学习平台。v2.3 新增个性化“10分钟复习清单”，把已有错题、识图错误和模拟故障成绩整理成可以立即执行的复习任务。平台不提供真实端子、电压或接线指导，匿名学习档案继续兼容旧备份。

> **仅用于教学模拟。** 不得用于真实设备诊断，不得替代持证电工、设备说明书或现场安全规程。本项目不提供带电测量、拆线、短接、送电或强制设备动作的指导。

## 功能范围

- 根据当前设备上的学习记录生成10分钟复习清单，无记录时提供安全的起步任务；
- 5分钟首次体验，不写入正式成绩，也不改变课程进度；
- 3门课程、9个章节的学习地图、完成状态与顺序解锁；
- 14个电气控制核心术语的集中解释；
- 3门课程、9个章节共60道教学题，每次章节测验随机抽取5题并即时解释；
- 每门课程提供10题综合评测，达到70%后标记为课程完成；
- 按安全、元件、控制逻辑、故障排查和识图能力生成掌握报告与复习路线；
- 章节测验、通过状态、答题正确率和错题优先复习；
- 错题逐项解释、对应知识卡和相似题复习入口；
- 每章统一显示“知识卡—测验—引导实验—随机练习—总结”学习路径；
- 完成模拟实验后生成实验目的、关键检查、结果和复盘问题；
- 直接启动：6种常见模拟故障；
- 正反转控制：8种常见模拟故障与方向分支；
- 点动与连续运行：6种模拟故障、三类现象与自锁保持逻辑；
- 跨实验综合训练：随机选择实验和故障，完成后纳入对应实验统计；
- 报告显示核心知识、最早偏离推荐路径的位置和下一步学习建议；
- 随机练习、自由诊断、评分、报告下载和学习中心；
- 引导学习模式、13张核心知识卡和不含真实接线信息的控制逻辑关系示意；
- 6个互动识图案例，记录首次判断得分、错误步骤和推荐路径；
- 1分钟新手引导，说明实验选择、模拟资料阅读和三种判断；
- 13张知识卡、60道题、20类模拟故障和6个识图案例均显示可追溯来源；
- 内容分为“已核对通用原理、部分核对、待复核”，待复核内容不进入课程综合评测；
- 根据最近错题推荐对应知识内容，复习后可返回当前实验继续练习；
- 每日完成1张知识卡、1次引导学习和2次随机练习，并显示连续学习天数；
- 按知识学习、引导完成和故障掌握计算三个实验的独立掌握度；
- 本机SQLite记录；免费云端部署使用临时记录，不承诺长期保存；
- 支持匿名JSON备份与恢复、TXT学习摘要和云端临时记录备份提醒；
- 不收集姓名、邮箱、账号或真实设备资料。

## 本机启动

需要 Python 3.11。

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

浏览器会自动打开应用。停止应用时在终端按 `Ctrl+C`。

## 开发与测试

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

学习中心使用原生Markdown表格，不使用 `st.dataframe` 或 `st.table`，以避免不同NumPy/PyArrow二进制组合导致的运行错误。

## 运行配置

| 环境变量 | 作用 |
| --- | --- |
| `DIANZHENTONG_ENV` | `local` 或 `community_cloud`；未设置时尝试自动识别 |
| `DIANZHENTONG_DB_PATH` | 覆盖SQLite数据库位置 |
| `DIANZHENTONG_ISSUES_URL` | 完整的HTTPS GitHub Issues地址；未配置时隐藏反馈按钮 |

本机数据默认保存在 `data/practice.db`，该文件已被Git忽略。Community Cloud默认使用系统临时目录，服务休眠、重启或更新后数据可能丢失。若SQLite不可用，应用会退化为内存记录，练习与报告功能仍可使用。

## 部署到 Streamlit Community Cloud

1. 在GitHub创建公开仓库 `dianzhentong`，不要提交本地数据库或密钥。
2. 将本项目的 `main` 分支推送到该仓库。
3. 在 Streamlit Community Cloud 新建应用，入口文件选择 `app.py`。
4. 在应用设置中配置：

   ```toml
   DIANZHENTONG_ENV = "community_cloud"
   DIANZHENTONG_ISSUES_URL = "https://github.com/MrHe-oss/dianzhentong/issues/new/choose"
   ```

5. 部署后检查首页、三个实验、互动识图、报告下载和学习中心，并确认页面显示“临时数据模式”。

当前公开仓库为 [MrHe-oss/dianzhentong](https://github.com/MrHe-oss/dianzhentong)，公开应用为 [dianzhentong.streamlit.app](https://dianzhentong.streamlit.app)。

## 项目结构

- `app.py`：Streamlit交互界面；
- `dianzhentong/experiments/`：按实验拆分的只读故障树；
- `dianzhentong/course.py`：课程、章节、解锁状态与实验学习记录；
- `dianzhentong/engine.py`：诊断状态与规则引擎；
- `dianzhentong/storage.py`：SQLite、学习活动、内存降级与统计；
- `dianzhentong/progress.py`：每日任务、连续学习和实验掌握度；
- `dianzhentong/backup.py`：匿名学习档案导出、校验、去重恢复与摘要；
- `dianzhentong/quiz.py`：章节题库、抽题、评分和测验记录结构；
- `dianzhentong/config.py`：公开版运行环境和反馈配置；
- `tests/`：自动化验收测试。

## 反馈与贡献

程序故障和专业内容纠错使用GitHub Issue模板。不要上传真实设备、单位、人员或生产信息。参见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [SECURITY.md](SECURITY.md)。

本项目采用 [MIT License](LICENSE)。
