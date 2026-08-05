# 学习数据（公测）

> `beta: true` — 5 个端点都是公测，可能调整。
> memo-context Step 1 的核心：拉今日清单 + 拉全量记录。

## 端点列表

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/study/get_today_items](#post-studyget_today_items) | POST | 墨墨 App 首页"今日学习"列表（含已学）| ✅ 常用 |
| [/study/query_study_records](#post-studyquery_study_records) | POST | 拉全量学习记录（客户端筛 today/due/VAGUE）| ✅ 常用 |
| [/study/get_study_progress](#post-studyget_study_progress) | POST | 今日学习进度 | 🔶 备用 |
| [/study/add_words](#post-studyadd_words) | POST | 添加单词到学习列表 | ❌ 暂不用 |
| [/study/advance_study](#post-studyadvance_study) | POST | 把已学单词的复习提前 | ❌ 暂不用 |

---

## POST /study/get_today_items

**用途：** 墨墨 App 首页"今日学习"列表。**注意：包含今天已学 + 未学**（看 `is_finished` 区分）。

跟 `query_study_records + next_study_date 过滤` 不一样：
- `get_today_items` = 墨墨 App 今日列表（含已学/未学/今日新学）
- `query_study_records + filter next_study_date` = 复习调度器算出来的"该学"清单

memo-context 默认用 `get_today_items`（更直接），用户说"讲没记住的"时才切到 `query_study_records` 筛 VAGUE/STICKING。

### Request

```json
{
  "is_finished": false,
  "is_new": false,
  "voc_ids": ["voc-..."],
  "spellings": ["apple"],
  "limit": 50
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `is_finished` | bool | 否 | 筛选"是否已完成" |
| `is_new` | bool | 否 | 筛选"是否新学" |
| `voc_ids` | string[] | 否 | 按 ID 查，**最多 1000**，忽略其他条件 |
| `spellings` | string[] | 否 | 按拼写查，**最多 1000**，与 voc_ids 二选一 |
| `limit` | int | 否 | 最多 1000，**默认 50** |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "today_items": [
      {
        "voc_id": "voc-...",
        "voc_spelling": "apple",
        "order": 1,
        "first_response": "FAMILIAR",
        "is_new": false,
        "is_finished": true
      }
    ]
  },
  "success": true
}
```

| 字段 | 类型 | 含义 |
|---|---|---|
| `voc_id` | string | 单词 ID |
| `voc_spelling` | string | 单词拼写 |
| `order` | int | 学习顺序（墨墨 App 里点哪个先学哪个）|
| `first_response` | enum | 第一次学习结果（`FAMILIAR/VAGUE/FORGET/WELL_FAMILIAR/CANCEL_WELL_FAMILIAR`）|
| `is_new` | bool | 是否新学 |
| `is_finished` | bool | 当日是否已完成 |

### 真实样例（2026-08-03 验证）

```python
import requests
r = requests.post(
    f"{BASE}/study/get_today_items",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={},  # 不带 filter
)
items = r.json()["data"]["today_items"]
# → 55 个（你今天完成的全部 task）

# 只看未学完
r = requests.post(f"{BASE}/study/get_today_items",
    json={"is_finished": False})
unfinished = r.json()["data"]["today_items"]

# 只看新学
r = requests.post(f"{BASE}/study/get_today_items",
    json={"is_new": True})
new_words = r.json()["data"]["today_items"]  # 你今天 0 个
```

---

## POST /study/query_study_records

**用途：** 拉全量学习记录。memo-context Step 1 主入口。

### Request

```json
{
  "next_study_date": {
    "start": "2026-08-03T00:00:00+08:00",
    "end": "2026-08-03T23:59:59+08:00"
  },
  "voc_ids": ["voc-..."],
  "spellings": ["apple"],
  "as_count": false,
  "limit": 50
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `next_study_date.start` | ISO 8601 北京时区 | 否 | `next_study_date >= start` |
| `next_study_date.end` | ISO 8601 北京时区 | 否 | `next_study_date <= end` |
| `voc_ids` | string[] | 否 | 按 ID 查，最多 1000，**忽略其他条件** |
| `spellings` | string[] | 否 | 按拼写查，最多 1000，与 voc_ids 二选一 |
| `as_count` | bool | 否 | true 时只返回 `count`，不返回 `records` |
| `limit` | int | 否 | 最多 1000，**默认 50** |

**时区注意：** `next_study_date` 参数是**北京时区 ISO 8601**（如 `"2026-08-03T00:00:00+08:00"`），但**返回的 `next_study_date` 字段是 UTC `16:00:00.000Z`**（anchor 当天 0 点北京时间）。

### Response (200)

```json
{
  "errors": [],
  "data": {
    "records": [
      {
        "voc_id": "voc-...",
        "voc_spelling": "apple",
        "add_date": "2026-07-09T20:55:29.000Z",
        "first_study_date": "2026-07-09T16:00:00.000Z",
        "last_study_date": "2026-08-01T16:00:00.000Z",
        "next_study_date": "2026-08-08T16:00:00.000Z",
        "last_response": "FAMILIAR",
        "study_count": 2,
        "tags": ["STICKING"]
      }
    ],
    "count": 200
  },
  "success": true
}
```

| 字段 | 类型 | 含义 |
|---|---|---|
| `voc_id` | string | 单词 ID |
| `voc_spelling` | string | 单词拼写 |
| `add_date` | UTC ISO | 加入词库时间 |
| `first_study_date` | UTC ISO | 首次学习时间 |
| `last_study_date` | UTC ISO | 最近学习时间 |
| `next_study_date` | UTC ISO (`16:00:00.000Z` anchor) | 下次该复习时间 |
| `last_response` | enum | 上次学习结果（见 index.md 枚举）|
| `study_count` | int | 学习次数（每日最多计入 1 次）|
| `tags` | enum[] | `STICKING / WELL_FAMILIAR` |

### 客户端筛选"今天 due"（memo-context Step 1 默认模式）

```python
TODAY = "2026-08-03"  # 北京时间今天

# 拉全量
r = requests.post(f"{BASE}/study/query_study_records",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"limit": 1000})  # 全量库一般 < 200
records = r.json()["data"]["records"]

# 客户端筛今天 due（用字符串前缀匹配，避开时区换算）
due_today = [r for r in records if r["next_study_date"].startswith(TODAY)]
# → 7 个：assert, chop, permit, prioritize, faith, anticipation, approval
```

### 客户端筛选"没记住的"（memo-context Step 1 备选模式）

```python
unstable = [r for r in records
            if "STICKING" in r.get("tags", [])
            or r["last_response"] in ("VAGUE", "FORGET")
            or r["next_study_date"].startswith(TODAY)]
```

### 服务端筛选（推荐，节省流量）

```python
# 服务端筛"今天 due"（用北京时区 ISO 8601）
r = requests.post(f"{BASE}/study/query_study_records",
    json={"next_study_date": {
        "start": "2026-08-03T00:00:00+08:00",
        "end": "2026-08-03T23:59:59+08:00"
    }})
today_due = r.json()["data"]["records"]
```

---

## POST /study/get_study_progress

**用途：** 今日学习进度（已完成/总数/学习时长）。

### Request

```json
{}
```

### Response (200)

```json
{
  "errors": [],
  "data": {
    "progress": {
      "finished": 55,
      "total": 55,
      "study_time": 777203
    }
  },
  "success": true
}
```

| 字段 | 类型 | 含义 |
|---|---|---|
| `finished` | int | 已完成单词数 |
| `total` | int | 今日应完成单词数 |
| `study_time` | int | 今日学习时长（毫秒）|

### 真实样例（2026-08-03 22:40 验证）

```python
r = requests.post(f"{BASE}/study/get_study_progress",
    headers={"Authorization": f"Bearer {TOKEN}"}, json={})
# → finished=55, total=55, study_time=777203 (≈ 13 分钟)
# 用户今天已学完！
```

---

## POST /study/add_words

**用途：** 添加单词到学习列表（公测）。

### Request

```json
{
  "words": [{"id": "voc-..."}],
  "advance": false
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `words` | {id: string}[] | ✅ | 单词 ID 列表，**最多 1000** |
| `advance` | bool | ✅ | 是否一并提前复习（无等级限制）|

### Response

```json
{"errors": [], "data": {"added_count": 114}, "success": true}
```

`added_count` 可能小于 words 数量（单词上限不足 / 已添加过）。

---

## POST /study/advance_study

**用途：** 把已学单词的复习提前到今天（公测）。

### Request

```json
{"voc_ids": ["voc-...", "voc-..."]}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `voc_ids` | string[] | ✅ | 最多 1000 |

### Response

```json
{"errors": [], "data": {"advanced_count": 514}, "success": true}
```
