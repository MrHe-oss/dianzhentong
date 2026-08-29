# 电诊通（Dianzhentong）

电诊通是面向电气工程及其自动化专业学生的故障排查教学原型。公开测试版 v0.7 提供“三相异步电动机直接启动”和“三相异步电动机正反转控制”两个实验，支持随机隐藏故障、自动评分、错因分析、推荐排查顺序、薄弱项练习和按实验统计。

> **仅用于教学模拟。** 不得用于真实设备诊断，不得替代持证电工、设备说明书或现场安全规程。本项目不提供带电测量、拆线、短接、送电或强制设备动作的指导。

## 功能范围

- 直接启动：6种常见模拟故障；
- 正反转控制：8种常见模拟故障与方向分支；
- 随机练习、自由诊断、评分、报告下载和学习中心；
- 本机SQLite记录；免费云端部署使用临时记录，不承诺长期保存；
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

5. 部署后检查首页、两个实验、报告下载和学习中心，并确认页面显示“临时数据模式”。

当前公开仓库为 [MrHe-oss/dianzhentong](https://github.com/MrHe-oss/dianzhentong)。最终应用URL将在 Streamlit Community Cloud 实际创建后补充。

## 项目结构

- `app.py`：Streamlit交互界面；
- `dianzhentong/experiments/`：按实验拆分的只读故障树；
- `dianzhentong/engine.py`：诊断状态与规则引擎；
- `dianzhentong/storage.py`：SQLite、内存降级与学习统计；
- `dianzhentong/config.py`：公开版运行环境和反馈配置；
- `tests/`：自动化验收测试。

## 反馈与贡献

程序故障和专业内容纠错使用GitHub Issue模板。不要上传真实设备、单位、人员或生产信息。参见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [SECURITY.md](SECURITY.md)。

本项目采用 [MIT License](LICENSE)。
