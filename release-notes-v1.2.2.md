# S16 冠军模拟器 v1.2.2 — 官方赛果自动同步

## 更新内容

### 新增 sync_scores.py：官方赛果一键同步
- 接入 **LoL Esports 官方数据接口**（`esports-api.lolesports.com`，官方前端公开 key，国内直连可用）
- 自动拉取 Worlds 淘汰赛完赛结果，更新页面 `FIXED` 常量与顶部副标题，无需再手动报比分
- 按 LINK 结构自动推导半决赛/决赛配对；同对取最近一场 + 淘汰赛日期过滤，规避瑞士轮重赛干扰
- 支持 `--dry-run` 预览；输出 `NO_CHANGE` / `UPDATED:` 供定时任务判断

### 配套定时自动化
- WorkBuddy 每日 10:00 自动执行：有新赛果 → 自动刷新托管链接 + 本地提交 + 更新笔记；推仓库 / Release 仍由用户确认

### 页面微调
- 副标题同步展示未完赛场次（如「四分之一决赛 DK vs BLG」），信息更完整

## 三入口
- WorkBuddy 托管：https://s16-champion-simulator.app.workbuddy.host/?sharecode=VUYT4KG5HD
- GitHub Pages：https://lbwb2013.github.io/LOL-S16-Champion-Simulator/
- Gitee Pages：https://johnny-silver-hand123.gitee.io/lol-s16-champion-simulator/
