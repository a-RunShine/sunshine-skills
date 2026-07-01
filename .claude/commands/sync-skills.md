---
description: "Mirror ~/.claude/skills/ into repo root, rewrite README skill table, then git commit + push. Project-level command for sunshine-skills."
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep]
---

# /sync-skills

把 `~/.claude/skills/` 下的 skills 镜像同步到当前仓库根目录，刷新 `README.md` 里的 skill 表格，然后 `git add` + `git commit` + `git push` 到 `origin/master`。

## 行为契约

1. **全量覆盖**：源中有则同步/更新；源中无且不在保护名单中的目录**删除**；源中新增的同步进来
2. **保护名单（永不删除/覆盖）**：`.git`, `.gitignore`, `.claude/`, `README.md`, `LICENSE`, `.DS_Store`, `.env`, `.env.example`
3. **rsync 作用域**：只针对每个 skill 子目录（`$SRC/$skill/` → `$DST/$skill/`），**不针对仓库根**，物理上不可能误删顶层项目文件
4. **gitignore 兼容**：
   - rsync 用 `--filter='dir-merge,- .gitignore'` 沿用 skill 自带 `.gitignore`
   - `git add` 沿用仓库根 `.gitignore`（覆盖 `.DS_Store`、`.env*`、`find-skill/cache/` 等）
5. **隐藏文件**：源中 `.*` 整体跳过同步（避免 `.env`、`.DS_Store` 透传）
6. **README 表格**：从每个 skill 的 `SKILL.md` 提取 `description:` 第一行重写 `## 包含的 Skills` 段；表格外的段落（包括底部"两个 find-skill 重复"提示、`## 添加方式`、`## License`）全部保留
7. **commit 格式**：`chore: sync skills from ~/.claude/skills/ @ <ISO8601 UTC>` + 多行 body 列出 add/update/remove
8. **错误处理**：`set -euo pipefail`，任一步失败立即终止；不 commit/push

## 不做的事

- 不创建空 commit（同步前后无差异时直接结束，提示 "Nothing to sync"）
- 不 force push；push 被拒时**保留 commit**，要求用户手动 rebase
- 不动 `~/.claude/skills/` 本身（只读源）
- 不动用户工作区中未提交的修改（启动时若脏则 abort）
- 不重写 README 中表格之外的段落

## 工作流

> **重要**：下面所有命令在仓库根目录运行，假设 cwd 已经是 `/Users/sunshine/Desktop/my-skills/`。Claude Code 触发 slash command 时自然就是当前项目目录。

### Step 1 — Preflight checks

```bash
set -eo pipefail
SRC="$HOME/.claude/skills"
DST="$(pwd)"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 保护名单：永不删除/覆盖
PROTECTED=(.git .gitignore .claude README.md LICENSE .DS_Store .env .env.example)

[ -d "$SRC" ] || { echo "ABORT: source $SRC not found"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "ABORT: not a git repo"; exit 1; }
git diff --quiet HEAD || { echo "ABORT: working tree has uncommitted changes"; git status --short; exit 1; }
```

> **兼容性注**：脚本故意不用 `set -u` 和 `mapfile` / `find -printf`，保持与 macOS 默认 bash 3.2 + BSD find 兼容。

如果 preflight 失败，**立即停止**，不要进入下一步。

### Step 2 — Compute diff（按子目录名算 ADD / UPDATE / REMOVE）

```bash
# 源：只取非隐藏的子目录（BSD find 兼容：先 find 出路径，sed 抠 basename）
SRC_DIRS=()
while IFS= read -r d; do
  [ -n "$d" ] && SRC_DIRS+=("$d")
done < <(find "$SRC" -mindepth 1 -maxdepth 1 -type d -not -name '.*' | sed 's|.*/||' | sort)

# 目标：所有第一层 entry
DST_ENTRIES=()
while IFS= read -r e; do
  [ -n "$e" ] && DST_ENTRIES+=("$e")
done < <(find "$DST" -mindepth 1 -maxdepth 1 | sed 's|.*/||' | sort)

# 三态分类（O(n*m) 简单查找；n<20 时足够快）
TO_ADD=()
TO_UPDATE=()
TO_REMOVE=()
TO_KEEP_PROTECTED=()

# 差集 1: 源中每个 → UPDATE 或 ADD
for d in "${SRC_DIRS[@]+"${SRC_DIRS[@]}"}"; do
  found=0
  for e in "${DST_ENTRIES[@]+"${DST_ENTRIES[@]}"}"; do
    [ "$d" = "$e" ] && { found=1; break; }
  done
  if [ "$found" -eq 1 ]; then
    TO_UPDATE+=("$d")
  else
    TO_ADD+=("$d")
  fi
done

# 差集 2: 目标中每个 → 源中也有则跳过；否则检查保护名单
for e in "${DST_ENTRIES[@]+"${DST_ENTRIES[@]}"}"; do
  found=0
  for d in "${SRC_DIRS[@]+"${SRC_DIRS[@]}"}"; do
    [ "$d" = "$e" ] && { found=1; break; }
  done
  [ "$found" -eq 1 ] && continue
  is_protected=0
  for p in "${PROTECTED[@]+"${PROTECTED[@]}"}"; do
    [ "$e" = "$p" ] && { is_protected=1; break; }
  done
  if [ "$is_protected" -eq 1 ]; then
    TO_KEEP_PROTECTED+=("$e")
  else
    TO_REMOVE+=("$e")
  fi
done

# 安全输出（处理空数组）
[ ${#TO_ADD[@]} -gt 0 ]            && ADD_STR="${TO_ADD[*]}"            || ADD_STR="(none)"
[ ${#TO_UPDATE[@]} -gt 0 ]         && UPDATE_STR="${TO_UPDATE[*]}"      || UPDATE_STR="(none)"
[ ${#TO_REMOVE[@]} -gt 0 ]         && REMOVE_STR="${TO_REMOVE[*]}"      || REMOVE_STR="(none)"
[ ${#TO_KEEP_PROTECTED[@]} -gt 0 ] && PROTECTED_STR="${TO_KEEP_PROTECTED[*]}" || PROTECTED_STR="(none)"
```

### Step 3 — Dry-run 预览 + 显式确认

```bash
echo "=== Sync Plan @ $TS ==="
echo "Will ADD (${#TO_ADD[@]}):       $ADD_STR"
echo "Will UPDATE (${#TO_UPDATE[@]}): $UPDATE_STR"
echo "Will REMOVE (${#TO_REMOVE[@]}): $REMOVE_STR"
echo "PROTECTED (kept):               $PROTECTED_STR"
echo
read -p "Type 'yes' to proceed (anything else to cancel): " ans
[ "$ans" = "yes" ] || { echo "Cancelled."; exit 0; }
```

**安全护栏**：
- 默认 dry-run 模式让用户看清会改什么
- 必须显式输入 `yes` 才会执行（不是 y，不是 Y）
- 其他任何输入都取消

### Step 4 — Rsync 同步 ADD / UPDATE

```bash
RSYNC_OPTS=(
  -a
  --delete
  --exclude='.git/'
  --filter='dir-merge,- .gitignore'
)

for skill in "${TO_ADD[@]}" "${TO_UPDATE[@]}"; do
  echo ">>> rsync $skill/"
  rsync "${RSYNC_OPTS[@]}" "$SRC/$skill/" "$DST/$skill/"
done
```

**为什么 `--delete` 在这里是安全的**：
- rsync 只对单个 skill 子目录操作（`$DST/$skill/`）
- skill 内部多余的脏文件被删掉是符合预期的（同步就是镜像）
- 不会触及 `$DST/.gitignore`、`$DST/README.md` 等顶层项目文件

### Step 5 — 删除 REMOVE 列表（双层保护）

```bash
for skill in "${TO_REMOVE[@]}"; do
  # 第二层防护：即使 Step 2 分类漏判，这里也会拦住
  case "$skill" in
    .git|.gitignore|.claude|README.md|LICENSE|.DS_Store|.env|.env.example)
      echo "REFUSE to remove protected: $skill"
      exit 1
      ;;
  esac
  echo ">>> rm $skill/"
  rm -rf "./$skill"
done
```

### Step 6 — 提取各 skill 的 description，重写 README 表格

```bash
# 6.1 用 awk 从每个 skill 的 SKILL.md 提取 description 第一行
TMP_TABLE="$(mktemp -t readme_table.XXXXXX)"
{
  echo "| Skill | 说明 |"
  echo "|---|---|"
  for skill in "${TO_ADD[@]}" "${TO_UPDATE[@]}"; do
    desc=$(awk '
      /^---$/{ c++; next }
      c==1 && /^description:[[:space:]]*/{
        sub(/^description:[[:space:]]*/, "")
        print
        exit
      }
    ' "$SRC/$skill/SKILL.md" 2>/dev/null)
    [ -z "$desc" ] && desc="(无 SKILL.md 描述)"
    # 截断到 60 字符（保护 README 表格排版）+ 转义表格里的 |
    if [ "${#desc}" -gt 60 ]; then
      desc="${desc:0:60}…"
    fi
    desc_escaped=$(printf '%s' "$desc" | sed 's/|/\\|/g')
    echo "| [$skill](./$skill/) | $desc_escaped |"
  done
} > "$TMP_TABLE"

# 6.2 用 python3 替换 README.md 的 "## 包含的 Skills" 段
python3 - "$TMP_TABLE" <<'PY'
import re, pathlib, sys
new_table = pathlib.Path(sys.argv[1]).read_text().rstrip()
readme = pathlib.Path("README.md")
text = readme.read_text()
# 匹配 "## 包含的 Skills\n\n" 后到下一个 "## " 之前（保留其后所有段落）
pat = re.compile(r"(## 包含的 Skills\n\n).*?(?=\n## |\Z)", re.S)
new_text, n = pat.subn(r"\1" + new_table + "\n\n", text, count=1)
if n == 0:
    print("ABORT: README.md has no '## 包含的 Skills' section; refusing to rewrite")
    sys.exit(1)
readme.write_text(new_text)
print(f"README.md updated ({len(new_table)} chars in skill table)")
PY

rm -f "$TMP_TABLE"
```

**README 改写范围**：
- ✅ 替换 `## 包含的 Skills` 段
- ✅ 保留底部"两个 find-skill 重复"提示
- ✅ 保留 `## 添加方式`、`## License`、GitHub badges 段落

### Step 7 — Stage、no-op 检测、commit、push

```bash
# 7.1 stage
git add -A

# 7.2 no-op 检测：没有变更就不 commit/push
if git diff --cached --quiet; then
  echo "Nothing to sync (no changes). Done."
  exit 0
fi

# 7.3 commit
git commit \
  -m "chore: sync skills from ~/.claude/skills/ @ $TS" \
  -m "Added: $ADD_STR" \
  -m "Updated: $UPDATE_STR" \
  -m "Removed: $REMOVE_STR" \
  -m "" \
  -m "Source: $SRC"

# 7.4 push（失败时保留 commit，提示用户手动 rebase）
git push origin master || {
  echo
  echo "WARN: push failed (likely non-fast-forward). Commit preserved locally."
  echo "Recovery: git pull --rebase && git push"
  exit 1
}

echo
echo "=== Sync done @ $TS ==="
echo "Committed and pushed: $(git rev-parse --short HEAD)"
```

## 边界情况处理

| 场景 | 行为 |
|------|------|
| 源 `~/.claude/skills/` 不存在 | Step 1 abort |
| 不在 git 仓库中 | Step 1 abort |
| 工作区有未提交修改 | Step 1 abort 并打印 `git status` |
| 同步前后内容完全一致 | Step 7.2 输出 "Nothing to sync" 退出，**不创建空 commit** |
| 源 skill 没有 `SKILL.md` | 表格里写 "(无 SKILL.md 描述)"，同步照常进行 |
| 源 skill 的 `SKILL.md` 没有 `description:` 字段 | 同上，表格里写 "(无 SKILL.md 描述)" |
| push 被远端拒绝（非快进） | commit 保留本地，提示 `git pull --rebase && git push` |
| `~/.claude/skills/` 下有 `.*` 隐藏子目录 | Step 2 整体跳过（不进入 ADD/UPDATE/REMOVE） |
| 仓库根有非 skill 子目录（如未来新增 `scripts/`） | 会出现在 REMOVE 列表 → dry-run 让用户决定 |
| `README.md` 没有 `## 包含的 Skills` 段 | Step 6.2 abort，不动 README |

## 所需 bash 权限

`settings.local.json` 需在 `permissions.allow` 数组中追加以下条目（如果还没放过）：

```json
"Bash(rsync *)",
"Bash(find *)",
"Bash(date *)",
"Bash(python3 - <<*)",
"Bash(python3 -c *)",
"Bash(python3 - *)",
"Bash(set *)",
"Bash(mapfile *)",
"Bash(declare *)",
"Bash(case *)",
"Bash([ *)",
"Bash(read *)",
"Bash(awk *)",
"Bash(sed *)",
"Bash(printf *)",
"Bash(mktemp *)",
"Bash(rm -f *)"
```

## 验证清单

执行后请跑以下场景验证：

1. **dry-run 行为**
   - 在 `~/.claude/skills/` 临时建 `test-skill/SKILL.md`
   - 跑 `/sync-skills`，确认 dry-run 显示 `Will ADD: test-skill`
   - 输入非 `yes` 不执行
   - 输入 `yes` 后同步完成，README 表格新增一行
   - 删掉 `test-skill` 再跑，dry-run 显示 `Will REMOVE: test-skill`

2. **保护名单**
   - `touch .gitignore` 修改仓库根 .gitignore
   - 跑 sync —— 确认 `.gitignore` 不出现在 REMOVE 列表
   - 仓库根 `mkdir foo-skill`，跑 sync —— 确认 `foo-skill` 出现在 REMOVE 列表并被删除

3. **空 diff 跳过 commit**
   - 连续跑两次 sync，第二次输出 "Nothing to sync" 并 exit 0
   - `git log` 不应出现空 commit

4. **脏工作区阻塞**
   - 仓库根 `echo xxx > README.md` 不 add
   - 跑 sync —— 应 abort 并打印 `git status`

5. **远端冲突**
   - 在 GitHub 网页 push 一个 commit
   - 本地跑 sync —— commit 应保留，push 失败并提示 rebase

6. **README 表格回归**
   - 同步前后 diff README.md，确认只改 `## 包含的 Skills` 段
   - 底部"两个 find-skill 重复"提示、`## 添加方式`、`## License` 完整保留
   - description 取自各 SKILL.md 第一行

7. **权限回归**
   - 第一次跑若提示权限被拒，按"所需 bash 权限"章节补全 `settings.local.json`

## 回滚指引

| 场景 | 回滚命令 |
|------|---------|
| 误删非 skill 目录 | `git reset --hard HEAD@{1}`（push 前） |
| README 改错 | `git checkout -- README.md` |
| push 冲突需重写 | `git reset --soft HEAD~1`（保留变更、撤销 commit），手动 rebase 后再 push |
| 完全回滚 | `git reset --hard HEAD`（一键回到 sync 前，前提是未 push） |

## 相关文件

- 本命令文件：`/Users/sunshine/Desktop/my-skills/.claude/commands/sync-skills.md`
- bash 权限：`.claude/settings.local.json`
- 同步源：`~/.claude/skills/`
- 远端：`https://github.com/a-RunShine/sunshine-skills.git` (master)
- 参考模板：`~/.claude/commands/install-skill.md`
