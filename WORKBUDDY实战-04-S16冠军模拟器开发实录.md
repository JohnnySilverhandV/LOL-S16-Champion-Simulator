# S16 全球总决赛冠军模拟器：从一张八强对阵截图到可玩交付

> 项目：LOL-S16-Champion-Simulator（GitHub：JohnnySilverhandV/LOL-S16-Champion-Simulator ｜ 码云：johnny-silver-hand123/LOL-S16-Champion-Simulator）
> 产出：单文件 HTML 对阵模拟器 · GitHub + 码云双仓库 + Release · WorkBuddy 托管 · localStorage 存档
> 技术栈：原生 HTML/CSS/JS · Git 双远端 · GitHub/Gitee API
> 当前版本：**v1.2.0**（2026-11-04 上线）

---

## 更新点（迭代记录）

### v1.2.0 — 官方赛果固定机制

真实比赛开打了：TES 1:3 IG。需求是把已打完的场次从「模拟」变成「事实」：

- 新增 `FIXED` 常量集中管理官方赛果，**加载时 `applyFixed()` 强制覆盖存档**——老用户哪怕之前模拟过别的比分，打开页面即被修正为官方结果，无需重置
- 已完赛场次三重拦截：弹窗无 ＋/− 按钮、`chScore`/`confirmScore` 直接 return、`unlock` 对固定场次无效（**不渲染解锁按钮**，而非仅置灰）
- 「重置模拟」只清未固定场次，官方赛果永久保留——`blank()` 里也预置赛果，重置后依然正确
- 视觉区分：手动锁定是金色 🔒，官方完赛是青色边框 + `🏁 已完赛`，弹窗只读大比分（胜者绿）
- 后续维护成本极低：每轮打完只需往 `FIXED` 加一行 `id:[按teams顺序的比分]`

设计要点：**「事实」和「用户输入」要分层**。官方赛果不属于用户可编辑状态，放常量而非存档里，天然免疫存档污染。

### v1.2.x 同日 — 码云绑定与双仓库同步

用户要求国内代码库同步更新，一次做完：

**1. Gitee 绑定**
- 私人令牌验证：`GET /api/v5/user`，实际登录名 ≠ 手机号（手机号只是登录手机），仓库路径用 login
- 凭据走 `git credential approve` 存入 Windows 凭据管理器，URL 不带 token，不入仓库
- 建仓 `auto_init:false`（否则初始提交会和 push 冲突）；仓库名与 GitHub 同一英文，码云同样别用中文

**2. 双推配置**
- `git remote set-url --add --push origin <gitee>` 挂第二个 push 地址，`git push origin main` 一条命令推两边
- **顺序改为「码云先、GitHub 后」**：GitHub 走代理不稳，先落袋稳定的码云
- gitee 配 `http.https://gitee.com/.proxy ""` 强制直连（国内站绕代理更快）；SSL 例外收窄为仅 `http.https://github.com/.*`

**3. Gitee Release ×5**
- `POST /repos/{o}/{r}/releases` 批量建 v1.0.0~v1.2.0，附件用 `POST .../releases/{id}/attach_files`（multipart）
- **Gitee Pages 已于 2024-05 官方下线**（入口 404、API 405），网上的"最新教程"全是过期洗稿——国内静态托管别再指望它

**4. GitHub 代理抖动的兜底方案（本次最有价值）**
- 现象：`api.github.com` 经代理稳定 200，但 `github.com` 主站 CONNECT 成功率仅约 1/3（502/SSL EOF）
- git push 直连 `github.com` 反复失败 → **改走 Contents API 直接更新文件**：`PUT /repos/{o}/{r}/contents/README.md`（带旧 sha），API 域名稳定所以必成
- API 生成的 commit 与本地分叉（同内容不同 hash）→ `git fetch` + `git rebase origin/main`，重复 patch 被 drop，历史干净
- 码云侧用 `push --force` 收敛指针——**仅当两边 tree 内容一致时 force 才安全**，先 diff 再 force
- 附带发现：Gitee 对脚本 UA 全站 403 反爬，验证内容要么浏览器要么带 token 的 API，raw 链接对匿名脚本不可用

### v1.1.0 — 规则修正 / 交互增强 / 移动端

上一版交给用户试玩后，收回四条反馈，逐条对应到改动：

**1. BO5 规则写错（真 bug）**
初版比分上限给到 5，允许出现 3:3，这是规则错误。修正为：
- 单队上限 `WIN_TARGET = 3`，败方上限 `MAX_LOSE = 2`
- 一方先到 3 后，另一方最多只能加到 2（按钮同步置灰）
- 确认条件收紧为「胜者必须恰好 3 胜」，未打完不允许锁定

**2. 时间线不连贯 → 连接线 + 时间轴**
- 顶部新增三节点时间轴（四分之一 11.04—11.07 → 半决赛 11.08—11.09 → 总决赛 11.15），赛段全部锁定后节点与连线点亮
- 对阵卡片之间用 SVG 绘制晋级连线：**不在 CSS 里硬画，而是渲染后按 `getBoundingClientRect()` 实测坐标生成肘形 path**，窗口缩放时防抖重绘。这样列宽、卡片高度随内容变化都不会错位

**3. 缺锁定功能 → 确认即锁定 + 冲突拦截**
- 确认比分即写入 `state.locked[id]`，卡片变金框 🔒，比分不可再改，需手动解锁
- 难点在于「改上游比分会不会悄悄改掉已定比赛」：把推导逻辑抽成纯函数 `buildState(scores)`，确认前先用克隆的比分试算一遍，若任何已锁定场次的参赛队伍会变，直接拒绝并提示先解锁

**4. 没做移动端 → 窄屏竖排**
- ≤900px 时对阵图从横向三列切成纵向堆叠，隐藏连接线，用虚线分隔赛段；弹窗、比分区、字号同步缩放，390px 以下再收一档

### v1.1.1 — 视觉：队伍圆点 + 银色奖杯

用户逐队点名要求圆点配色，并按位置描述双色：

| 战队 | 圆点实现 |
|---|---|
| TES | 橙红 + 同色光晕 |
| IG | 白色 + 白光晕 |
| GEN | `linear-gradient(90deg, 暗黄 0 50%, 黑 50% 100%)` 左右对分 |
| LYON | 金色 |
| DK | 纯黑 + 1px 白描边（否则深色背景上直接隐身） |
| BLG | `radial-gradient(circle at 72% 28%, 粉 0 36%, 浅蓝 46% 100%)` 右上角粉高光 |
| T1 | 正红 |
| KC | 浅蓝（v1.1.2 加深为 #2ea8ff） |

冠军奖杯：原本金色 🏆，改为银色系——emoji 无法直接改色，用 `filter: grayscale(1) brightness(1.62) contrast(.92)` + 双层银白 drop-shadow 做出银质高光，冠军卡边框/文字同步转银。

### v1.1.2 — 选手名专属配色

- **GEN**：名字用渐变文字，左半暗黄、右半黑
- **BLG**：名字最后一个字母拆成 `<span>` 染粉色发光（Bin→Bi**n**）
- **DK**：名字纯黑
- **KC**：圆点从 `#9fe4ff` 加深到 `#2ea8ff`

> 踩坑：纯黑文字在深色毛玻璃上不可读。解法是给文字加极细的浅色 `drop-shadow` 描边，既保住「黑色」的视觉要求，又不至于看不见。渐变文字同理——`background-clip:text` + `color:transparent` 后 text-shadow 失效，只能用 filter 描边。

### 迭代方法论小结

1. 「确认即锁定」这类状态，最好在写入前用**纯函数试算**做冲突检测，比事后回滚干净得多
2. 连线的正确做法是量布局画 SVG，不是用伪元素拼边界
3. 用户用「左边/右边」「右上角」描述颜色时，说的是**圆点内部的方位**，直接上渐变（linear/radial）即可还原
4. 配色迭代用版本号切片（v1.1.0 功能 / v1.1.1 圆点 / v1.1.2 名字），每次一个 commit + 一个 Release，回滚成本极低
5. **官方事实数据放常量、用户输入放存档**，加载时单向覆盖，存档污染问题根治
6. **主站被墙/抖动时，API 域名往往是独立通道**（api.github.com ≠ github.com），git push 走不通就用 Contents API 改文件，再 rebase 收敛历史
7. 双仓库同步要「先推稳的」：码云直连永远先推，GitHub 抖动不影响国内侧交付

---

## 以下为 v1.0 原始开发复盘（保留原文）

## 一、需求拆解

用户给了一张 S16 八强对阵截图，需求一句话但信息量不小：

1. 八强固定，四强/决赛/冠军由用户**点击选择赢家**来模拟
2. 点击对阵时弹出**5v5 对位框**：上路 Theshy 对 369、打野、中路、下路、辅助逐行对照
3. 比分可调（如 IG 3:2 TES），确认后胜者自动晋级下一轮
4. 界面美观、毛玻璃效果、不需要头像（纯文字）、时间线写上

## 二、核心设计：树状级联重算

模拟器最容易做错的地方是「改了前面的比分，后面轮次没跟着变」。方案是把整个淘汰赛建成状态机：

- `state.scores` 存每场比分，`state.teams` 存每场参赛队
- `winnerOf(id)` 由比分算胜者；`propagate()` 把胜者沿 `LINK` 映射表向下传递
- **关键规则**：下游场次队伍发生变化时，自动清空该场比分并继续级联——保证任何时刻数据自洽
- 决赛胜出即写入 `state.champion`，冠军卡点亮

这样「IG 3:2 TES → 确认 → 胜者填入半决赛空位 → 改成 3:1 → 半决赛队伍重算、比分清零」全链路自动完成，不需要用户手动撤销。

比分调节用 ± 按钮限制 0~5，确认时拦截两种非法状态：0:0（未模拟）和 a:b（BO5 平局），拦截时 shake 动画提示。

> v1.1.0 起该段已被 `buildState()` 纯函数 + 锁定机制取代，保留以记录演进。

## 三、UI：毛玻璃 + 状态可视化

- 背景 3 个大 blur 光斑做缓慢漂移动画（keyframes drift），营造霓虹氛围
- 卡片 `backdrop-filter: blur(16px)` + 半透明边框，hover 上浮 + 边框发光
- 胜者行绿色发光、败者行降透明度、未定队伍显示「? 待定」，一眼能读出晋级状态
- 弹窗按 上路/打野/中路/下路/辅助 五行排布，左右队名各染队伍色，中间 VS 渐变字
- 冠军卡独立一列，金色描边 + 奖杯 glow 动画

## 四、踩坑实录（本次最有价值的部分）

### 坑 1：GitHub 仓库名不支持中文

用 API 创建 `LOL-S16-冠军模拟器`，返回 201，但 `full_name` 是 `LOL-S16--`——**GitHub 静默剔除了中文字符**，连报错都没有。处理：PATCH 改名为 `LOL-S16-Champion-Simulator`。教训：涉及 GitHub 资源命名，中文一律换英文，且建完必须回读 `full_name` 验证。

### 坑 2：Windows schannel 证书吊销检查失败

本地走代理 `127.0.0.1:55566`，CONNECT 隧道能建立，但 TLS 握手报 `CRYPT_E_NO_REVOCATION_CHECK (0x80092012)`——schannel 无法验证证书吊销状态。两个解法：

- curl：加 `--ssl-no-revoke`
- git：设 `http.schannelCheckRevoke=false` / `http.sslNoRevoke=true`（本例中单靠这个没生效）

补充：代理软件重启后端口会变（55566 → 59893 → 50107），**不要在仓库里写死代理端口**，让 git 走环境变量 `https_proxy` 更稳。

### 坑 3：代理是 MITM 模式，OpenSSL 后端不认其证书

换 `http.sslBackend=openssl` 后报 `unable to get local issuer certificate (20)`——代理对流量做了中间人替换证书。最终对本仓库一次性放行，并在 v1.2.x 收窄为**按域名配置**，码云走正常证书校验：

```bash
git config http.https://github.com/.sslBackend openssl
git config http.https://github.com/.sslVerify false   # 仅 github.com 域生效
git config http.https://gitee.com/.proxy ""           # 码云直连，不碰代理
```

排障路径：先分网络（baidu 200 / github 000 确认是域名级屏蔽而非断网）→ 再分代理有无（`-x` 显式指定 / `--noproxy "*"`）→ 再看 verbose 输出定位到 schannel → 最后才动 SSL 校验开关。

### 坑 4：本地预览服务器被回收

`python -m http.server &` 起的进程在命令结束时被回收，浏览器打开显示代码而非页面。正确姿势是用受管后台任务启动（run_in_background），再截图验证，验完显式 stop。

## 五、交付形态

- 单文件 HTML，零依赖，双击即开，符合「离线优先」交付约定
- 模拟进度存 localStorage（键 `s16bracket_v2`），刷新不丢，一键重置
- 代码约 640 行（v1.2.0），状态机与渲染分离

## 六、可复用结论

1. 竞技赛事模拟器通用骨架：**固定首轮种子 + LINK 映射 + 级联重算**，任何杯赛（8 强/16 强/双败）都能套
2. 改状态前先想清楚「下游数据怎么失效」，比事后写撤销逻辑省一半代码
3. Windows + 代理环境访问 GitHub 的三板斧：`--ssl-no-revoke`、`http.sslNoRevoke`、`http.sslVerify=false`（限定仓库）
4. GitHub API 建仓后必须回读验证名称，中文字符会被静默吞掉
5. 多端发布要一次做全：WorkBuddy 托管给不折腾的用户，GitHub Pages/Release 给开发者，码云 Release 给国内下载，三者同一份 HTML 源码
6. 双仓库 = 双远端 + 双推顺序（稳的先推），一条 `git push` 同步两边

---

## 上线地址

- WorkBuddy 托管（国内直连）：https://s16-champion-simulator.app.workbuddy.host/?sharecode=VUYT4KG5HD
- GitHub Pages：https://johnnysilverhandv.github.io/LOL-S16-Champion-Simulator/s16-bracket.html
- GitHub 仓库：https://github.com/JohnnySilverhandV/LOL-S16-Champion-Simulator
- 码云仓库（国内直连）：https://gitee.com/johnny-silver-hand123/LOL-S16-Champion-Simulator
- Release：GitHub 与码云各 5 个（v1.0.0~v1.2.0，v1.2.0 附最新 HTML）
