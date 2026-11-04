# LOL-S16-Champion-Simulator · S16 全球总决赛冠军模拟器

一个**单文件、零依赖**的《英雄联盟》S16 全球总决赛淘汰赛模拟器。八强已定，冠军由你决定——点开对阵、设置比分、看着胜者一路杀进决赛，举起召唤师奖杯。

> 🎮 **在线直接玩（国内直连）**：<https://s16-champion-simulator.app.workbuddy.host/?sharecode=VUYT4KG5HD>
>
> 🌐 **GitHub Pages**：<https://johnnysilverhandv.github.io/LOL-S16-Champion-Simulator/s16-bracket.html>
>
> 🇨🇳 **码云仓库（国内直连）**：<https://gitee.com/johnny-silver-hand123/LOL-S16-Champion-Simulator>
>
> 📦 **离线版下载**：[GitHub Releases](https://github.com/JohnnySilverhandV/LOL-S16-Champion-Simulator/releases) ｜ [码云 Releases](https://gitee.com/johnny-silver-hand123/LOL-S16-Champion-Simulator/releases)

---

## 🆕 更新日志

### v1.2.0 — 官方赛果接入（2026-11-04）

- **TES 1 : 3 IG 已完赛**：作为官方赛果固定写死，IG 自动晋级半决赛
- 该场**不可模拟、不可调比分、不可解锁**；点开只读查看 5v5 对位与最终比分
- 卡片用青色边框 + `🏁 已完赛 / 官方赛果 · 不可修改` 标记，与手动锁定的金色区分
- **重置模拟不会清掉官方赛果**，只清未固定场次
- 旧存档自动修正：此前模拟过 TES vs IG 的浏览器，打开即被强制覆盖为官方比分

### v1.1.2 — 选手名配色细化

- GEN：队员名左半暗黄、右半黑（渐变文字，浅描边保证黑段可读）
- BLG：队员名最后一个字母粉色发光（Bi**n**、Xu**n**、Knigh**t**、Vipe**r**、O**N**）
- DK：队员名纯黑 + 浅描边（纯黑无描边在深色毛玻璃上会直接隐身）
- KC：小圆点蓝色加深

### v1.1.1 — 视觉微调

- 8 支队伍圆点按品牌色重制：TES 橙红 / IG 白 / GEN 左暗黄右黑 / LYON 金 / DK 黑（描边保证可见）/ BLG 浅蓝 + 右上粉高光 / T1 正红 / KC 蓝
- 冠军奖杯与冠军卡改为**银色系**（召唤师杯质感）

### v1.1.0 — 规则与体验修正

- **BO5 规则收紧**：单队比分上限 3，杜绝 3:3；胜者必须拿满 3 胜才能确认
- **对阵连接线**：轮次之间 SVG 连线可视化，已锁定的晋级链路点亮发光
- **顶部时间线轴**：四分之一决赛 → 半决赛 → 总决赛，赛段全部打完后节点点亮
- **比分锁定**：确认比分即锁定（🔒），可手动解锁；若改上游比分会影响已锁定场次，直接拦截并提示
- **移动端适配**：窄屏自动切换竖排布局，弹窗、比分区、字体全部自适应

### v1.0.0 — 首版

- 完整淘汰赛对阵图（八强 → 半决赛 → 总决赛 → 冠军）
- 点击对阵弹出 5v5 对位，可调比分，胜者自动晋级
- 毛玻璃 UI + localStorage 本地存档

---

## ✨ 功能

- **完整淘汰赛对阵图**：四分之一决赛 → 半决赛 → 总决赛 → 冠军展示卡，SVG 连接线 + 顶部时间线轴，赛程与官方一致
- **点击对阵弹出 5v5 对位**：上路 / 打野 / 中路 / 下路 / 辅助逐行对照（TheShy 对 369、Faker 对 Knight……）
- **BO5 比分模拟**：先到 3 胜者晋级，败方最多 2 分，3:3 无法出现
- **比分锁定**：确认即锁定，防误改；可手动解锁；改上游比分若影响已锁定场次会被拦截
- **官方赛果固定**：已打完的场次写死真实比分，不可模拟、不可解锁，重置也不清空
- **级联重算**：比分一改，后续轮次的参赛队伍自动重算，数据永远自洽
- **冠军卡点亮**：总决赛打完，银色召唤师杯 + 冠军队名登基
- **本地存档**：模拟进度存 localStorage，刷新不丢
- **移动端适配**：手机窄屏竖排布局，单手可玩
- **毛玻璃视觉**：深色霓虹背景 + blur 玻璃卡片，赛博朋克风

## 🏁 已完赛赛果

| 日期 | 对阵 | 比分 | 晋级 |
|---|---|---|---|
| 11月04日 06:00 | TES vs IG | **1 : 3** | IG |

> 已完赛场次在页面中以青色边框 + `🏁 已完赛` 标识，比分只读。

## 🏆 S16 八强名单

| 战队 | 上单 | 打野 | 中单 | 下路 | 辅助 |
|---|---|---|---|---|---|
| IG | TheShy | Wei | Rookie | JiaQi | Meiko |
| TES | 369 | Tian | Creme | JackeyLove | Zhuo |
| BLG | Bin | Xun | Knight | Viper | ON |
| GEN | Kiin | Canyon | Chovy | Ruler | Duro |
| DK | Siwoo | Lucid | ShowMaker | Smash | Career |
| T1 | Doran | Oner | Faker | Peyz | Keria |
| KC | Canna | Yike | kyeahoo | Caliste | Busio |
| LYON | Dhokla | Inspired | Saint | Berserker | Isles |

## 🚀 使用

无需安装、无需构建——**双击 `s16-bracket.html` 即可离线运行**，或直接访问上面的在线链接。

## 🛠 技术要点

- 纯原生 HTML/CSS/JS，单文件零框架零依赖
- 淘汰赛状态机：`scores` + `teams` 两张表，`LINK` 映射 + 级联重算，任何杯赛结构可复用
- `buildState(scores)` 纯函数：由比分推导全部参赛队伍与胜者，锁定冲突校验靠它试算，避免状态互相污染
- 官方赛果用 `FIXED` 常量集中管理，加载时强制覆盖存档，天然兼容旧数据
- 连接线按真实布局 DOM 测量后绘制 SVG，窗口缩放自适应
- 毛玻璃：`backdrop-filter: blur()` + 动态光斑背景

## 📄 License

MIT
