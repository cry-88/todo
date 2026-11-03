# GitHub 五仓库「营业状态」盘点

> 盘点时间：2026-10-29 · 更新：2026-11-03（island 真实版上线、somethings-else 开店后修订）
> 结论先行：**5 个仓库里 3 个完全营业、1 个半营业（差一台 VPS）、1 个不需要营业。**

## 总览

| 仓库 | 是什么 | 营业状态 | 缺什么 |
|---|---|---|---|
| [stargazers-log](https://github.com/cry-88/stargazers-log) | GitHub star 事件日志页 | 🟢 **完全营业** | 无（数据更新靠快照，另说） |
| [island-wave-cards](https://github.com/cry-88/island-wave-cards) | 匿名卡片站（看过即消失） | 🟢 **完全营业**（11-03 真实版上线） | 无 |
| [kubao-support-agent](https://github.com/cry-88/kubao-support-agent) | 在线智能客服（对话/工单/看板） | 🟡 半营业（静态预览在线，完整版缺席） | 一台 VPS（全套部署脚本已备好） |
| [somethings-else](https://github.com/cry-88/somethings-else) | 作品集（个人名片页等） | 🟢 **完全营业**（10-29 已开店） | 无（陆续推新项目上去即可） |
| [todo](https://github.com/cry-88/todo) | 学习日记 + 每日 demo | ⚪ 不需要营业（日记本不是饭店） | 无（里面的名片页可顺手上线） |

营业状态判定标准：别人打开一个网址，能不能真的用上你的东西。

---

## 逐仓详查

### 🟢 stargazers-log —— 完全营业

- **在线地址**：https://cry-88.github.io/stargazers-log/ （实测 HTTP 200）
- **架构**：纯静态页（index.html + script.js + events.json），无后端。`deploy.yml` 在每次 push 到 main 时自动发布 Pages
- **为什么它成了**：它从设计上就不需要后端——数据是 `events.json` 快照，前端读本地 JSON 渲染。零依赖 + Pages = 天然完全体
- **唯一的小尾巴**：`events.json` 是静态快照，你新 star 一个仓库不会自动出现在页面上（workflow 只部署、不拉新数据）。想要"自动更新"需要加一个定时任务去调 GitHub API 再 commit——这是另一个话题了

### 🟢 island-wave-cards —— 完全营业（2026-11-03 真实版上线）

- **真实版在线地址**：https://island-wave-cards.app.workbuddy.host/?sharecode=R7PJGFFCEZ （手机号/微信登录，全球可访问）
- **演示版**：https://cry-88.github.io/island-wave-cards/ （Pages 根入口，localStorage 本地后端，零门槛试玩，页顶有去真实版的入口）
- **上线过程实测确认的架构真相**：
  - 云服务「激活」和「发布」是两步——只激活不发静态站，访客打不开；只发静态站不激活，后端 404。两步都做，数据平面才挂到域名上
  - **Origin 白名单实测为真**：带 `Origin: https://cry-88.github.io` 的请求被云端 403 拒绝——所以真实版只能住 WorkBuddy 托管域，Pages 域名下放真实版会「打得开、登不上」，故 Pages 根入口放演示版
- **架构回顾**：纯静态前端 + WorkBuddy 托管云服务（Database + Auth），`cards` / `card_seen` 两表 + 5 条 RLS 策略，「看过即消失」由服务端 `NOT EXISTS` 子查询强制执行——后端「永不信任前端」的教科书案例
- **排障收获**：CI 翻车过一次（`cp` 多源文件目标写成文件路径 → run 失败，修复后重跑 20 秒过）——「本地跑通 ≠ CI 跑通」，且部署失败时旧站点毫发无损，这就是流水线的意义

### 🟡 kubao-support-agent —— 半营业（差一台服务器）

- **在线地址**：https://cry-88.github.io/kubao-support-agent/ （实测 HTTP 200）
- **Pages 上是静态预览**：workflow 把 `assets/runtime.js` 改写成 `__CS_MODE__='static'`，页面不发任何后端请求，"只做界面演示"——README 原话
- **完整版是真的完整**：`node server.js` 后端零依赖（Node ≥ 18 内置模块）+ `schema.sql` 数据库 + 多轮对话/工单队列/管理后台全都有
- **部署脚本是专业级的**：`deploy/` 下有 nginx 反代（TLS + 真实 IP 透传）、systemd 常驻（开机自启/崩溃重启）、install.sh（幂等安装）、rollback.sh（切软链回滚）、backup.sh（含口令的备份，权限 600，保留 14 天）
- **但从未执行过**：`docs/stage6-deploy.md` 第一段原话——「**全部命令仅生成，未执行任何一条。本会话没有可用的 SSH 连接**」
- **补店清单**：一台 VPS（+域名+HTTPS 证书），然后按 stage6 文档逐条执行（文档自己提醒了：每条标了风险等级和回滚方式，review 后再跑）。这是四个项目里唯一"功能全乎、只差饭店"的
- **安全提醒**：README 自己写了「部署后第一件事：改管理员口令，默认口令仅用于开发演示」

### 🟢 somethings-else —— 完全营业（2026-10-29 开店）

- **在线地址**：https://cry-88.github.io/somethings-else/ （实测 HTTP 200，内容与本地文件分毫不差）
- **怎么开的**：一个 Pages workflow（`cp 个人名片页 → _site/index.html`）+ Settings→Pages→Source 选 GitHub Actions。单文件零依赖，push 后几十秒上线
- **性质**：作品集仓库，目前只有一个「个人名片页」（单文件 HTML，零依赖）
- **机制意义**：这是五个仓库里唯一有「自动营业机制」的——以后每 push 一个新项目，Pages 自动重新发布，再也不用手动碰设置

### ⚪ todo —— 不需要营业

- **性质**：学习日记仓库（PLAN.md、进度追踪、复盘卡片）+ 每日方向 demo
- 日记本不需要饭店。但 `01-frontend/index.html`（名片页）和 somethings-else 里那个是同一个东西——真想上线的话同理 10 分钟

---

## 补店优先级（按投入产出比）

1. ~~**somethings-else → Pages**~~ ✅ 已完成（10-29，约 10 分钟）
2. ~~**island-wave-cards → 激活云服务 + 部署真实版**~~ ✅ 已完成（11-03，含一次 CI 翻车修复）
3. **kubao-support-agent → 租 VPS 按 stage6 文档上线**（需要一点钱 + 一次认真的部署，正好是 D13 的实战教材）—— **只剩这一单**
4. stargazers-log 的 events.json 自动更新（锦上添花，可选）

> 这份盘点本身就是 D13（部署运维）的预习资料。到时候的真实体验路径建议：先用 somethings-else 十分钟走通「代码 → Pages → 公开网址」全流程建立信心，再拿 kubao 打 VPS 硬仗。
