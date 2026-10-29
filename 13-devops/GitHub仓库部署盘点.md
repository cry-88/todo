# GitHub 五仓库「营业状态」盘点

> 盘点时间：2026-10-29 · 触发事件：D2 笑话 API 明白了「GitHub 只存代码、不运行代码」
> 结论先行：**5 个仓库里 2 个完全营业、2 个半营业（只有演示/预览版在线）、1 个不需要营业、1 个完全没营业。**

## 总览

| 仓库 | 是什么 | 营业状态 | 缺什么 |
|---|---|---|---|
| [stargazers-log](https://github.com/cry-88/stargazers-log) | GitHub star 事件日志页 | 🟢 **完全营业** | 无（数据更新靠快照，另说） |
| [island-wave-cards](https://github.com/cry-88/island-wave-cards) | 匿名卡片站（看过即消失） | 🟡 半营业（demo 在线，真实版缺席） | 云服务激活 + 真实版前端部署 |
| [kubao-support-agent](https://github.com/cry-88/kubao-support-agent) | 在线智能客服（对话/工单/看板） | 🟡 半营业（静态预览在线，完整版缺席） | 一台 VPS（全套部署脚本已备好） |
| [somethings-else](https://github.com/cry-88/somethings-else) | 作品集（个人名片页等） | 🔴 **完全没营业** | 一个 GitHub Pages workflow（约 10 分钟） |
| [todo](https://github.com/cry-88/todo) | 学习日记 + 每日 demo | ⚪ 不需要营业（日记本不是饭店） | 无（里面的名片页可顺手上线） |

营业状态判定标准：别人打开一个网址，能不能真的用上你的东西。

---

## 逐仓详查

### 🟢 stargazers-log —— 完全营业

- **在线地址**：https://cry-88.github.io/stargazers-log/ （实测 HTTP 200）
- **架构**：纯静态页（index.html + script.js + events.json），无后端。`deploy.yml` 在每次 push 到 main 时自动发布 Pages
- **为什么它成了**：它从设计上就不需要后端——数据是 `events.json` 快照，前端读本地 JSON 渲染。零依赖 + Pages = 天然完全体
- **唯一的小尾巴**：`events.json` 是静态快照，你新 star 一个仓库不会自动出现在页面上（workflow 只部署、不拉新数据）。想要"自动更新"需要加一个定时任务去调 GitHub API 再 commit——这是另一个话题了

### 🟡 island-wave-cards —— 半营业

- **在线地址**：https://cry-88.github.io/island-wave-cards/ （实测 HTTP 200）
- **但要小心**：Pages 上跑的是 `demo.html`（workflow 里 `cp frontend/demo.html _site/index.html`）——**数据存在每个访客自己的浏览器 localStorage 里**。你在 demo 里写的卡片，别人看不到；这就是 D2 笑话 API 的同款问题
- **真实版的架构其实很聪明**：`backend/server.js` 的注释写明「真实后端不在这里——账号与数据由 WorkBuddy 托管云服务（Database + Auth）提供，前端通过云端 SDK 直连，服务端 RLS 策略强制执行『看过即消失』」
  - 也就是说：它**不需要自己租饭店**，Pages 托管前端 + 云服务存数据 = 完整营业
- **为什么还差一步**：`frontend/config.js` 里三个值全是占位符（`YOUR-APP-PREFIX` / `wbpk_YOUR_PUBLISHABLE_KEY`）——云服务从未激活，真实版从未上线
- **补店清单**：① 激活 WorkBuddy 云服务拿真配置 ② 把真实版 `index.html` 也传上 Pages（workflow 里加一行 cp）
- **顺带一个 D2 知识点的印证**：RLS（行级安全策略）= "看过即消失"这条规则由数据库强制执行，而不是靠前端自觉——和后端"永不信任前端"是同一条法则

### 🟡 kubao-support-agent —— 半营业（差一台服务器）

- **在线地址**：https://cry-88.github.io/kubao-support-agent/ （实测 HTTP 200）
- **Pages 上是静态预览**：workflow 把 `assets/runtime.js` 改写成 `__CS_MODE__='static'`，页面不发任何后端请求，"只做界面演示"——README 原话
- **完整版是真的完整**：`node server.js` 后端零依赖（Node ≥ 18 内置模块）+ `schema.sql` 数据库 + 多轮对话/工单队列/管理后台全都有
- **部署脚本是专业级的**：`deploy/` 下有 nginx 反代（TLS + 真实 IP 透传）、systemd 常驻（开机自启/崩溃重启）、install.sh（幂等安装）、rollback.sh（切软链回滚）、backup.sh（含口令的备份，权限 600，保留 14 天）
- **但从未执行过**：`docs/stage6-deploy.md` 第一段原话——「**全部命令仅生成，未执行任何一条。本会话没有可用的 SSH 连接**」
- **补店清单**：一台 VPS（+域名+HTTPS 证书），然后按 stage6 文档逐条执行（文档自己提醒了：每条标了风险等级和回滚方式，review 后再跑）。这是四个项目里唯一"功能全乎、只差饭店"的
- **安全提醒**：README 自己写了「部署后第一件事：改管理员口令，默认口令仅用于开发演示」

### 🔴 somethings-else —— 完全没营业（最该补）

- **没有在线地址**。没有 `.github/workflows/`，没有 Pages 配置
- **性质**：作品集仓库，目前只有一个「个人名片页」（单文件 HTML，零依赖）
- **尴尬之处**：作品集的使命就是"给别人看"，但它现在只有菜谱没有饭店——别人只能读代码想象效果，看不到成品。**这是五个仓库里投入产出比最高的一单**
- **补店清单**：一个 Pages workflow（抄 stargazers-log 的 `deploy.yml`，path 改一下），push 后即得 `https://cry-88.github.io/somethings-else/`。预计 10 分钟，零依赖零构建，无任何风险

### ⚪ todo —— 不需要营业

- **性质**：学习日记仓库（PLAN.md、进度追踪、复盘卡片）+ 每日方向 demo
- 日记本不需要饭店。但 `01-frontend/index.html`（名片页）和 somethings-else 里那个是同一个东西——真想上线的话同理 10 分钟

---

## 补店优先级（按投入产出比）

1. **somethings-else → Pages**（10 分钟，零风险，作品集终于能"看"不能仅"读"）
2. **island-wave-cards → 激活云服务 + 部署真实版**（架构已就绪，只差配置；需要先用免费额度激活云服务）
3. **kubao-support-agent → 租 VPS 按 stage6 文档上线**（需要一点钱 + 一次认真的部署，正好是 D13 的实战教材）
4. stargazers-log 的 events.json 自动更新（锦上添花，可选）

> 这份盘点本身就是 D13（部署运维）的预习资料。到时候的真实体验路径建议：先用 somethings-else 十分钟走通「代码 → Pages → 公开网址」全流程建立信心，再拿 kubao 打 VPS 硬仗。
