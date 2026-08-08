# lark-send: 飞书 image + Markdown 发送

## 关键命令

### 1. Markdown 介绍消息

```bash
lark-cli im +messages-send \
  --as bot \
  --user-id ou_48931ee833d5c20d0d37927b3b6a917f \
  --markdown '**今天薄弱词 24 个**（VAGUE 24 + FORGET 0 + STICKING 0），分 2 张大图讲解 ✓'
```

**必须 `--as bot`**，否则报 `missing required scope(s): im:message.send_as_user`（user 身份没权限）。

**外层必须单引号**，否则反引号（`` `code` ``）被 bash 当 command substitution 吃。

### 2. 图片消息

```bash
# cwd 必须是项目根，cd 到 .today-weak 后再发图
cd <项目根>/.today-weak   # 必先 cd
lark-cli im +messages-send \
  --as bot \
  --user-id ou_48931ee833d5c20d0d37927b3b6a917f \
  --file weakness-part1.jpg
```

**关键 3 条**：
1. **必须 `cd <dir>`** — `--file` 是 cwd-relative basename
2. **不能用绝对路径** — 报 "absolute paths and .. are rejected"
3. **不能用 `..`** — 同样被拒

## 完整发送脚本（render_and_send.py 实现）

```python
import subprocess
import os
from pathlib import Path

USER_ID = "ou_48931ee833d5c20d0d37927b3b6a917f"
INTRO = """**今天薄弱词 {N} 个**（VAGUE {v} + FORGET {f} + STICKING {s}），分 {k} 张大图讲解 ✓"""

def send_intro(n: int, v: int, f: int, s: int, k: int, dry_run: bool = True):
    msg = INTRO.format(N=n, v=v, f=f, s=s, k=k)
    if dry_run:
        print(f"[DRY-RUN] would send intro: {msg}")
        return True
    r = subprocess.run(
        [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--user-id", USER_ID,
            "--markdown", msg,  # msg 已经在 Python 字符串里，没 bash 解释问题
        ],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"[WARN] intro send failed: {r.stderr}")
        return False
    print(f"[OK] intro sent")
    return True

def send_image(jpg_basename: str, dry_run: bool = True) -> bool:
    """jpg_basename 是 basename（cwd 已被切到 out_dir）"""
    if dry_run:
        print(f"[DRY-RUN] would send image: {jpg_basename}")
        return True
    r = subprocess.run(
        [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--user-id", USER_ID,
            "--file", jpg_basename,
        ],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"[WARN] image send failed ({jpg_basename}): {r.stderr}")
        return False
    print(f"[OK] image sent: {jpg_basename}")
    return True

def send_all(intro_args: tuple, jpg_paths: list[str], out_dir: str, dry_run: bool = True):
    """out_dir: .today-weak 绝对路径"""
    send_intro(*intro_args, dry_run=dry_run)
    cwd = os.getcwd()
    try:
        os.chdir(out_dir)  # 关键：切到 .today-weak
        for p in jpg_paths:
            send_image(os.path.basename(p), dry_run=dry_run)
    finally:
        os.chdir(cwd)
```

## 错误码速查

| 报错 | 原因 | 处理 |
|---|---|---|
| `missing required scope(s): im:message.send_as_user` | 漏 `--as bot` | 加 `--as bot` |
| `absolute paths and .. are rejected` | `--file` 用了绝对路径或 `..` | `cd <dir> && --file <basename>` |
| `connection refused` / `timeout` | lark-cli 没装或网络问题 | 检查 PATH，重试 |
| `image too large` | 文件 > 5MB | 压 JPEG（quality 88, 85% resize） |
| `user not found` | `--user-id` 错 | 检查 user_id = `ou_48931ee833d5c20d0d37927b3b6a917f` |

## 误发消息撤回

```bash
lark-cli im messages delete --as bot --message-id om_xxx --yes
```

`--yes` 是 high-risk-write 必须的。失败不"半撤回"——要么 OK 要么报错，幂等。

## 飞书身份备忘

- **bot 身份**：appId `cli_aacca75bca781be2`，默认有 im:message 权限
- **user 身份**：需要 `lark-cli auth login --scope "im:message.send_as_user"` 重授权
- **本 skill 全部用 bot 身份**（不需要重授权）
- **user_id = `ou_48931ee833d5c20d0d37927b3b6a917f`**（何东波，self DM）

## token 路径

- 墨墨 token：本 skill 自己的 `<skill_dir>/.env`（真文件，含 `MAIMEMO_TOKEN=...`）
- 飞书 token：lark-cli 内部管理（`~/.lark-cli/auth.json`），无需手动配
