#!/usr/bin/env python3
"""S16 冠军模拟器·官方赛果自动同步。

从 LoL Esports 官方数据接口（esports-api.lolesports.com）拉取 Worlds 淘汰赛
完赛结果，自动更新 s16-bracket.html 里的 FIXED 常量与页面副标题。

用法：
  python sync_scores.py            # 有更新则改文件
  python sync_scores.py --dry-run  # 只看不改

输出约定（供自动化流程判断）：
  无更新        → 最后一行打印 NO_CHANGE
  有更新        → 最后一行打印 UPDATED: <改动摘要>
  接口失败/异常 → 非零退出码

设计要点：
  - 队伍名用官方全名 → 括号代码 的别名表映射，大小写不敏感
  - 淘汰赛配对按 LINK 结构动态推导（qf1→sf1[0] ...），与 HTML 保持一致
  - 同一对阵取【最近一场】完赛记录，天然规避瑞士轮重赛干扰
  - 比分下标永远对应 HTML 里 MATCHES[id].teams 的顺序
"""
import argparse
import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

API = ("https://esports-api.lolesports.com/persisted/gw/getSchedule"
       "?hl=zh-CN&leagueId=98767975604431411")          # Worlds
API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"    # 官方前端公开 key
HTML = "s16-bracket.html"
KNOCKOUT_START = "2026-11-01"   # 淘汰赛起始（UTC），排除瑞士轮同队再交手

# 官方队伍全名（小写）→ 括号代码
ALIAS = {
    "invictus gaming": "IG",
    "top esports": "TES",
    "gen.g esports": "GEN",
    "bilibili gaming": "BLG",
    "dplus kia": "DK",
    "t1": "T1",
    "karmine corp": "KC",
    "lyon": "LYON",
    "lyon gaming": "LYON",
}

# 与 HTML 里 LINK 常量一致：来源场次 → (目标槽位, 下标)
LINK = {"qf1": ("sf1", 0), "qf2": ("sf1", 1), "qf3": ("sf2", 0),
        "qf4": ("sf2", 1), "sf1": ("fin", 0), "sf2": ("fin", 1)}
STAGE_NAME = {"qf": "四分之一决赛", "sf": "半决赛", "fin": "总决赛"}


def fetch_events():
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(API, headers={"x-api-key": API_KEY})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        data = json.load(r)
    return data["data"]["schedule"]["events"]


def parse_html(html):
    """从 HTML 提取 QF 配对与现有 FIXED。"""
    qf = {}
    for m in re.finditer(r'id:"(qf\d)"[^>\n]*teams:\["(\w+)","(\w+)"\]', html):
        qf[m.group(1)] = [m.group(2), m.group(3)]
    fixed = {}
    block = re.search(r"const FIXED = \{(.*?)\n\};", html, re.S)
    if block:
        for m in re.finditer(r"(qf\d|sf\d|fin):\s*\[(\d+),\s*(\d+)\]", block.group(1)):
            fixed[m.group(1)] = [int(m.group(2)), int(m.group(3))]
    return qf, fixed


def cst_date(start_time):
    """UTC 开赛时间 → 北京时间 '11月04日'。"""
    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    cst = dt.astimezone(timezone(timedelta(hours=8)))
    return f"{cst.month}月{cst.day}日"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    qf_pairs, fixed = parse_html(html)
    if not qf_pairs:
        print("✘ 未能从 HTML 解析 QF 配对", file=sys.stderr)
        return 2

    # 完赛记录：同一队伍组合取最近一场（规避瑞士轮重赛）
    results = {}   # frozenset(代码) -> {"scores": {代码: 分}, "date": str}
    for e in fetch_events():
        if e.get("state") != "completed":
            continue
        if e.get("startTime", "")[:10] < KNOCKOUT_START:
            continue
        teams = (e.get("match") or {}).get("teams") or []
        codes = []
        scores = {}
        for t in teams:
            code = ALIAS.get((t.get("name") or "").lower())
            if not code:
                codes = None
                break
            codes.append(code)
            scores[code] = ((t.get("result") or {}) or {}).get("gameWins", 0)
        if not codes or len(set(codes)) != 2:
            continue
        key = frozenset(codes)
        cur = results.get(key)
        if cur is None or e["startTime"] > cur["start"]:
            results[key] = {"start": e["startTime"], "date": cst_date(e["startTime"]),
                            "scores": scores}

    # 逐槽位推导：QF 配对固定，SF/FIN 由上一轮胜者组成
    slot_teams = dict(qf_pairs)   # id -> [A, B]（None 表示还定不出来）
    slot_res = {}                 # id -> {"date","scores":[A分,B分],"winner"}
    winners = {}
    for qid in ("qf1", "qf2", "qf3", "qf4"):
        r = results.get(frozenset(qf_pairs[qid]))
        if r:
            a, b = qf_pairs[qid]
            slot_res[qid] = {"date": r["date"], "scores": [r["scores"][a], r["scores"][b]],
                             "winner": a if r["scores"][a] > r["scores"][b] else b}
            winners[qid] = slot_res[qid]["winner"]
        else:
            winners[qid] = None
    for sid in ("sf1", "sf2", "fin"):
        if sid == "fin":
            src = [winners.get("sf1"), winners.get("sf2")]
        else:
            src = [winners.get(k) for k, (tgt, _) in LINK.items() if tgt == sid]
            src = [src[0], src[1]] if len(src) == 2 else [None, None]
        slot_teams[sid] = src if all(src) else None
        if slot_teams[sid]:
            r = results.get(frozenset(slot_teams[sid]))
            if r:
                a, b = slot_teams[sid]
                slot_res[sid] = {"date": r["date"], "scores": [r["scores"][a], r["scores"][b]],
                                 "winner": a if r["scores"][a] > r["scores"][b] else b}

    # 与现有 FIXED 对比
    updates = {}
    for sid, r in slot_res.items():
        old = fixed.get(sid)
        if old != r["scores"]:
            updates[sid] = r

    pending = [sid for sid in ("qf1", "qf2", "qf3", "qf4", "sf1", "sf2", "fin")
               if slot_teams.get(sid) and sid not in slot_res]
    if not updates:
        print("官方赛果无变化")
        for sid in pending:
            print(f"  · {STAGE_NAME[sid[:2] if sid[:2]!='fi' else 'fin']} "
                  f"{' vs '.join(slot_teams[sid])} 未完赛")
        print("NO_CHANGE")
        return 0

    # 重写 FIXED 块
    merged = dict(fixed)
    for sid, r in updates.items():
        merged[sid] = r["scores"]
    lines = ["const FIXED = {"]
    for sid in ("qf1", "qf2", "qf3", "qf4", "sf1", "sf2", "fin"):
        if sid in merged:
            r = slot_res.get(sid)
            teams = qf_pairs.get(sid) or slot_teams.get(sid)
            note = ""
            if r:
                stage = STAGE_NAME["fin" if sid == "fin" else sid[:2]]
                note = f'  // {r["date"]} {teams[0]} {r["scores"][0]} : {r["scores"][1]} {teams[1]} —— {r["winner"]} 晋级' \
                       + ("并夺冠" if sid == "fin" else "")
            lines.append(f'  {sid}: {merged[sid]},{note}')
    lines.append("};")
    new_block = "\n".join(lines)
    html = re.sub(r"const FIXED = \{.*?\n\};", new_block, html, count=1, flags=re.S)

    # 重写副标题
    done_parts = []
    for sid in ("qf1", "qf2", "qf3", "qf4", "sf1", "sf2", "fin"):
        r = slot_res.get(sid)
        if r:
            teams = qf_pairs.get(sid) or slot_teams.get(sid)
            stage = STAGE_NAME["fin" if sid == "fin" else sid[:2]]
            done_parts.append(f'{r["date"]} {teams[0]} {r["scores"][0]} : {r["scores"][1]} {teams[1]}'
                              f'（{r["winner"]} ' + ("夺冠" if sid == "fin" else "晋级") + "）")
    sub_parts = []
    if done_parts:
        sub_parts.append("已完赛：" + " · ".join(done_parts))
    for sid in pending:
        stage = STAGE_NAME["fin" if sid == "fin" else sid[:2]]
        sub_parts.append(f'{stage} {" vs ".join(slot_teams[sid])}')
    sub_parts += ["其余场次可模拟", "确认即锁定"]
    new_sub = "<p>" + " · ".join(sub_parts) + "</p>"
    html, n = re.subn(r"<p>已完赛：.*?确认即锁定</p>", new_sub, html, count=1)
    if n != 1:
        print("✘ 未能定位副标题段落", file=sys.stderr)
        return 2

    if not args.dry_run:
        with open(HTML, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)

    print("赛果更新：")
    for sid, r in updates.items():
        teams = qf_pairs.get(sid) or slot_teams.get(sid)
        print(f'  ✔ {sid}: {teams[0]} {r["scores"][0]} : {r["scores"][1]} {teams[1]}（{r["winner"]} 晋级）')
    print("UPDATED: " + ", ".join(f'{sid} {" ".join(map(str, r["scores"]))}' for sid, r in updates.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
