#!/usr/bin/env python3
"""一条命令完成发版：提交 -> 打 tag -> 双推(Gitee 先/GitHub 后) -> 双平台 Release -> 校验。

用法示例：
  python release.py v1.3.0 -m "fix: 修正比分上限" -n notes.md -a s16-bracket.html
  python release.py v1.3.0 -m "..." --dry-run

约定：
  - Gitee 直连（自动 no_proxy），GitHub 走环境变量代理（端口变了也不用改脚本）
  - 失败即中止并打印可执行的下一步，绝不静默跳过
  - 只负责 git + 两个平台的 Release；WorkBuddy 托管发布需在会话里另行触发
"""
import argparse
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

GITHUB_SSL = ssl._create_unverified_context()   # 本机代理为 MITM，需跳过校验
GITEE_HOST = "gitee.com"


# ---------------- 基础工具 ----------------
def log(msg, kind="info"):
    icon = {"info": "·", "ok": "✔", "warn": "!", "step": "→", "err": "✘"}[kind]
    print(f"{icon} {msg}", flush=True)


def run(cmd, check=True, env=None, quiet=True):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, env=e)
    if check and r.returncode != 0:
        out = (r.stdout + r.stderr).strip()
        log(f"命令失败：{' '.join(cmd) if isinstance(cmd, list) else cmd}\n{out}", "err")
        sys.exit(1)
    return (r.stdout or "").strip() if quiet else r


def git(*args, check=True, env=None):
    return run(["git", *args], check=check, env=env)


def git_credential(host):
    """从 Windows 凭据管理器取 username/password。"""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input=f"protocol=https\nhost={host}\n\n",
        capture_output=True, text=True,
    )
    user = token = None
    for line in (p.stdout or "").splitlines():
        if line.startswith("username="):
            user = line.split("=", 1)[1]
        elif line.startswith("password="):
            token = line.split("=", 1)[1]
    return user, token


def http(method, url, data=None, headers=None, ctx=None, use_proxy=True, raw_body=None):
    """统一请求；use_proxy=False 时绕过环境代理（Gitee 国内直连）。"""
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
    h.update(headers or {})
    body = raw_body if raw_body is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    handlers = []
    if not use_proxy:
        handlers.append(urllib.request.ProxyHandler({}))
    if ctx is not None:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(req, timeout=60) as r:
            payload = r.read()
            try:
                return r.status, json.loads(payload)
            except Exception:
                return r.status, payload
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"message": raw[:300]}
    except Exception as e:  # 网络层
        return 0, {"message": f"{type(e).__name__}: {e}"}


def multipart(fields, files):
    """files: {key: (filename, bytes, content_type)}"""
    b = "----rel" + uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (fn, content, ctype) in files.items():
        out += (
            f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode() + content + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return out, f"multipart/form-data; boundary={b}"


# ---------------- 平台适配 ----------------
class GitHub:
    def __init__(self, owner, repo):
        self.owner, self.repo = owner, repo
        self.token = git_credential("github.com")[1]
        if not self.token:
            log("取不到 GitHub 凭据（git credential 为空）", "err")
            sys.exit(1)

    @property
    def api(self):
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def _h(self, extra=None):
        h = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github+json"}
        h.update(extra or {})
        return h

    def ensure_release(self, tag, title, body):
        st, d = http("POST", f"{self.api}/releases", {"tag_name": tag, "name": title, "body": body, "draft": False, "prerelease": False},
                     self._h({"Content-Type": "application/json"}), GITHUB_SSL)
        if st in (200, 201):
            return d["id"], "created"
        st2, d2 = http("GET", f"{self.api}/releases/tags/{tag}", None, self._h(), GITHUB_SSL)
        if st2 == 200:
            return d2["id"], "existed"
        log(f"GitHub Release 创建失败：{d.get('message')}", "err")
        sys.exit(1)

    def upload(self, release_id, path):
        name = os.path.basename(path)
        ctype = "text/html" if name.endswith((".html", ".htm")) else "application/octet-stream"
        with open(path, "rb") as f:
            content = f.read()
        url = f"https://uploads.github.com/repos/{self.owner}/{self.repo}/releases/{release_id}/assets?name={name}"
        st, d = http("POST", url, None, self._h({"Content-Type": ctype}), GITHUB_SSL, raw_body=content)
        if st in (200, 201):
            log(f"GitHub 附件 {name} 上传成功（{len(content) // 1024} KB）", "ok")
        elif st == 422 and isinstance(d, dict) and "already_exists" in str(d.get("errors", "")):
            log(f"GitHub 附件 {name} 已存在，跳过", "warn")
        else:
            log(f"GitHub 附件 {name} 上传失败：{d.get('message')}", "err")
            sys.exit(1)


class Gitee:
    def __init__(self, owner, repo):
        self.owner, self.repo = owner, repo
        self.token = git_credential(GITEE_HOST)[1]
        if not self.token:
            log("取不到 Gitee 凭据（git credential 为空）", "err")
            sys.exit(1)

    @property
    def api(self):
        return f"https://gitee.com/api/v5/repos/{self.owner}/{self.repo}"

    def ensure_release(self, tag, title, body):
        st, d = http("POST", f"{self.api}/releases",
                     {"access_token": self.token, "tag_name": tag, "name": title,
                      "body": body, "target_commitish": "main", "prerelease": False},
                     {"Content-Type": "application/json"}, use_proxy=False)
        if st in (200, 201) and isinstance(d, dict) and d.get("id"):
            return d["id"], "created"
        st2, d2 = http("GET", f"{self.api}/releases/tags/{tag}?access_token={self.token}",
                       None, {}, use_proxy=False)
        if st2 == 200 and isinstance(d2, dict) and d2.get("id"):
            return d2["id"], "existed"
        log(f"Gitee Release 创建失败：{d.get('message') if isinstance(d, dict) else d}", "err")
        sys.exit(1)

    def upload(self, release_id, path):
        name = os.path.basename(path)
        ctype = "text/html" if name.endswith((".html", ".htm")) else "application/octet-stream"
        with open(path, "rb") as f:
            content = f.read()
        body, ct = multipart({"access_token": self.token}, {"file": (name, content, ctype)})
        st, d = http("POST", f"{self.api}/releases/{release_id}/attach_files", None,
                     {"Content-Type": ct}, use_proxy=False, raw_body=body)
        if st in (200, 201):
            log(f"Gitee 附件 {name} 上传成功（{len(content) // 1024} KB）", "ok")
        else:
            msg = d.get("message") if isinstance(d, dict) else d
            log(f"Gitee 附件 {name} 上传失败：{msg}", "err")
            sys.exit(1)


# ---------------- 主流程 ----------------
def slug_from_remote(url):
    url = url.rstrip("/").removesuffix(".git")
    parts = url.split("/")
    return parts[-2], parts[-1]


def push_with_retry(args, env=None, times=3, tag=""):
    for i in range(1, times + 1):
        r = run(["git", "push", *args], check=False, env=env, quiet=False)
        if r.returncode == 0:
            return True
        log(f"第 {i} 次推送失败，{6 * i}s 后重试…", "warn")
        time.sleep(6 * i)
    return False


def main():
    ap = argparse.ArgumentParser(description="一条命令发版")
    ap.add_argument("version", help="版本号，如 v1.3.0")
    ap.add_argument("-t", "--title", help="Release 标题（默认取版本号）")
    ap.add_argument("-m", "--message", help="git 提交信息（有未提交改动时必填）")
    ap.add_argument("-n", "--notes", help="Release 说明的 markdown 文件")
    ap.add_argument("-a", "--asset", action="append", default=[], help="Release 附件，可重复")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不执行")
    ap.add_argument("--no-release", action="store_true", help="只推 git，不建 Release")
    args = ap.parse_args()

    v = args.version if args.version.startswith("v") else "v" + args.version
    title = args.title or f"{os.path.basename(git('rev-parse', '--show-toplevel'))} {v}"

    body = ""
    if args.notes and os.path.exists(args.notes):
        body = open(args.notes, encoding="utf-8").read().strip()
    elif args.message:
        body = args.message

    log(f"发版 {v} — {title}", "step")

    # 1. 工作区
    dirty = git("status", "--porcelain")
    if dirty:
        if args.dry_run:
            log(f"工作区有 {len(dirty.splitlines())} 个未提交改动（dry-run 不处理，实跑需 -m）", "warn")
        elif not args.message:
            log("工作区有未提交改动，请用 -m 提供提交信息（会全量提交）", "err")
            print(dirty)
            sys.exit(1)
        else:
            log(f"待提交文件 {len(dirty.splitlines())} 个", "info")
            git("add", "-A")
            git("commit", "-m", args.message)
            log("已提交", "ok")

    # 2. tag
    existing = run(["git", "tag", "-l", v])
    if existing:
        log(f"tag {v} 已存在，跳过创建", "warn")
    else:
        if not args.dry_run:
            git("tag", "-a", v, "-m", title)
        log(f"打 tag {v}", "ok")

    # 3. 取远端
    gitee_url = git("remote", "get-url", "gitee", check=False) or ""
    gh_url = git("remote", "get-url", "origin", check=False) or ""
    if not gitee_url or "gitee.com" not in gitee_url:
        log("找不到 gitee 远端，先 git remote add gitee <url>", "err")
        sys.exit(1)
    if "github.com" not in gh_url:
        log("origin 不是 GitHub 地址，无法定位 GitHub 仓库", "err")
        sys.exit(1)
    g_owner, g_repo = slug_from_remote(gitee_url)
    h_owner, h_repo = slug_from_remote(gh_url)

    if args.dry_run:
        log("dry-run 计划：", "step")
        print(f"  仓库   Gitee {g_owner}/{g_repo} | GitHub {h_owner}/{h_repo}")
        print(f"  推送   gitee main+{v} -> origin main+{v}")
        print(f"  Release 双平台 {v}")
        print(f"  附件   {args.asset or '(无)'}")
        return

    # 4. 推送（Gitee 先，稳）
    log("推送 Gitee", "step")
    if not push_with_retry(["gitee", "main", v], env={"no_proxy": GITEE_HOST, "NO_PROXY": GITEE_HOST}):
        log("Gitee 推送失败，已中止（其他平台未动）", "err")
        sys.exit(1)
    log("Gitee 推送完成", "ok")

    log("推送 GitHub", "step")
    if not push_with_retry([gh_url, "main", v]):
        log("GitHub 推送失败（代理抖动？）。Gitee 已成功，可稍后单独重跑：", "err")
        print(f"  git push {gh_url} main {v}")
        sys.exit(2)
    log("GitHub 推送完成", "ok")

    # 5. Release
    if not args.no_release:
        gh = GitHub(h_owner, h_repo)
        rid, how = gh.ensure_release(v, title, body)
        log(f"GitHub Release {how}（id={rid}）", "ok")
        for a in args.asset:
            gh.upload(rid, a)

        gt = Gitee(g_owner, g_repo)
        gid, ghow = gt.ensure_release(v, title, body)
        log(f"Gitee Release {ghow}（id={gid}）", "ok")
        for a in args.asset:
            gt.upload(gid, a)

    # 6. 校验
    log("校验远端 tag", "step")
    for name, remote in (("Gitee", "gitee"), ("GitHub", gh_url)):
        out = run(["git", "ls-remote", remote, f"refs/tags/{v}"], check=False)
        log(f"{name} {v} {'已就位' if out else '缺失'}", "ok" if out else "err")

    print()
    log(f"{v} 发版完成。下一步：触发 WorkBuddy 托管重新发布（会话里说一声即可）", "ok")
    print("\n可直接粘贴到 README 更新日志的片段：\n")
    print(f"### {v} — {title}\n{body or '(待补充)'}\n")


if __name__ == "__main__":
    main()
