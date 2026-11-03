# LOL-S16-Champion-Simulator · S16 全球总决赛冠军模拟器

一个**单文件、零依赖**的《英雄联盟》S16 全球总决赛淘汰赛模拟器。八强已定，冠军由你决定——点开对阵、设置比分、看着胜者一路杀进决赛，举起召唤师奖杯。

> 🎮 **在线直接玩**：<https://johnnysilverhandv.github.io/LOL-S16-Champion-Simulator/s16-bracket.html>

## ✨ 功能

- **完整淘汰赛对阵图**：四分之一决赛（TES vs IG / GEN vs LYON / DK vs BLG / T1 vs KC）→ 半决赛 → 总决赛 → 冠军展示卡，赛程时间线与官方一致
- **点击对阵弹出 5v5 对位**：上路 / 打野 / 中路 / 下路 / 辅助逐行对照（TheShy 对 369、Faker 对 Knight……）
- **可调比分**：± 按钮 0~5 分，BO5 平局自动拦截；确认后胜者自动晋级下一轮
- **级联重算**：修改已赛比分，后续轮次队伍与比分自动重算，数据永远自洽
- **冠军卡点亮**：总决赛打完，奖杯 + 冠军队名登基
- **本地存档**：模拟进度存 localStorage，刷新不丢，一键重置
- **毛玻璃视觉**：深色霓虹背景 + blur 玻璃卡片，赛博朋克风

## 🚀 使用

无需安装、无需构建——**双击 `s16-bracket.html` 即可离线运行**，或直接访问上面的在线链接。

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

## 🛠 技术要点

- 纯原生 HTML/CSS/JS，约 400 行，零框架零依赖
- 淘汰赛状态机：`scores` + `teams` 两张表，`LINK` 映射 + 级联重算，任何杯赛结构可复用
- 毛玻璃：`backdrop-filter: blur()` + 动态光斑背景

## 📄 License

MIT
