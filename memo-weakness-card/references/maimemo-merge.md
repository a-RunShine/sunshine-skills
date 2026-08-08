# maimemo-merge: get_today_items × 2 合并去重

## 核心规则

**任意时点拉"今日学习列表"都必须合并 `is_finished=true` + `is_finished=false` 两次调用按 `voc_id` 去重**。单次调用会漏词。

## 详细文档

主文档在 `../memo-context/references/maimemo-api/study.md`（5 个端点完整 schema + 字段语义 + 限流 + 时区）。

本 reference 只列本 skill 用的关键点。

## 本 skill 用到的端点

### `POST /study/get_study_progress`（诊断用，不是词源）

```json
{
  "progress": {
    "finished": 21,
    "total": 55
  }
}
```

**仅用于日志**（"今天 21/55 已学"），不参与词源判断。

### `POST /study/get_today_items`（词源主路径）

```json
// Request
{
  "is_finished": true,   // 第一次 false, 第二次 true
  "limit": 200
}

// Response (单条)
{
  "voc_id": "abc123",
  "voc_spelling": "clinic",
  "first_response": "VAGUE",   // FAMILIAR / VAGUE / FORGET / WELL_FAMILIAR / CANCEL_WELL_FAMILIAR
  "is_new": true,              // 新词 vs 复习词
  "is_finished": true,         // 已学 vs 未学
  "tags": []                   // 可能含 STICKING / WELL_FAMILIAR
}
```

**关键 enum**：
- `first_response` = `FAMILIAR` / `VAGUE` / `FORGET`（**不是 FORGOT**）/ `WELL_FAMILIAR` / `CANCEL_WELL_FAMILIAR`
- `tags` ⊋ `STICKING`（粘）/`WELL_FAMILIAR`（熟）— 用户在墨墨 App 手动打的标签

## 合并去重代码模板

```python
import requests

API_BASE = "https://open.maimemo.com/open"
TOKEN = open(".claude/skills/memo-context/.env").read().split("=")[1].strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def get_today_items(is_finished: bool, limit: int = 200) -> list[dict]:
    r = requests.post(
        f"{API_BASE}/study/get_today_items",
        headers=HEADERS,
        json={"is_finished": is_finished, "limit": limit},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("items", [])

def fetch_all_today_words() -> list[dict]:
    """合并 is_finished=true + false 两次调用，按 voc_id 去重。"""
    finished   = get_today_items(is_finished=True,  limit=200)
    unfinished = get_today_items(is_finished=False, limit=200)
    seen = set()
    merged = []
    for it in finished + unfinished:
        vid = it["voc_id"]
        if vid in seen:
            continue
        seen.add(vid)
        merged.append(it)
    return merged  # 任何时点 = 55 词（= progress.total）
```

## 为什么必须合并（2026-08-06 当晚教训）

| 时刻 | progress | is_finished=true | is_finished=false | 合并去重 |
|---|---|---|---|---|
| 18:00 cron 跑 | 21/55 | 21 词 | 34 词 | **55 词** ✓ |
| 23:00+ 学完 | 55/55 | 55 词 | 0 词 | **55 词** ✓ |

- **只调 `is_finished=true` 一次**：18:00 跑漏 34 词
- **只调 `is_finished=false` 一次**：23:00+ 跑拿到 0 词（看似正常但前提是用户真学完了）
- **不要 fallback 到 `query_study_records` 全量库**（那会捞到历史所有词，不是"今日"语义）

## 弱信号筛 + 排序

```python
def is_weak(word: dict) -> bool:
    return (
        word.get("first_response") in {"VAGUE", "FORGET"}
        or "STICKING" in (word.get("tags") or [])
    )

PRIORITY = {"FORGET": 0, "VAGUE": 1, "STICKING": 2}

def sort_weak(words: list[dict]) -> list[dict]:
    weak = [w for w in words if is_weak(w)]
    def key(w):
        # 主键：弱信号优先级（FORGET 优先）
        # 次键：是否在 tags 里有 STICKING
        # 末键：study_count asc（学得少但弱 → 排前）
        main = PRIORITY.get(
            "FORGET" if w.get("first_response") == "FORGET"
            else "STICKING" if "STICKING" in (w.get("tags") or [])
            else "VAGUE",
            9
        )
        study_count = w.get("study_count", 999)
        return (main, study_count)
    return sorted(weak, key=key)
```

## 限流

- 墨墨背单词：10s/20req，60s/40req，5h/2000req
- 每次 Step 1 只调 2 次（get_study_progress + 2 × get_today_items）— **不**撞限流
- Step 2 拉 interpretations + phrases 时再 sleep 0.6s/call + 每 18 calls sleep 10s

## 时区 + 墨墨每日重置时间

- API 字段 `*_date` 是 UTC `16:00:00.000Z`（对应北京时间当天 0 点）
- "今天"判断：`voc["next_study_date"]` 或 `add_date` 字符串前缀匹配（不用做时区换算）
- 本 skill 不做日期判断（get_today_items 已经限定为今日）

**墨墨每日重置时间：凌晨 4:00**（不是自然日 0:00）：

- 0:00 - 3:59 本地时间跑脚本 → `get_today_items` 拿的是**昨天**的 55 词
- 4:00 - 23:59 本地时间跑脚本 → `get_today_items` 拿的是**今天**的 55 词

`weak.json` 的 `date` 字段用 `maimemo_today()` 函数算（4:00 切），与 `get_today_items` 语义一致。
