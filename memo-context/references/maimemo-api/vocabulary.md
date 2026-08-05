# 单词

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/vocabulary?spelling=...](#get-vocabularyspellingspelling) | GET | 按拼写查单个单词 | 🔶 备用 |
| [/vocabulary/query](#post-vocabularyquery) | POST | 批量查单词（spellings/ids 列表）| ✅ 常用 |

---

## GET /vocabulary?spelling=...

**用途：** 按拼写查单个单词基本信息（id, spelling）。**没有学习状态。**

memo-context 一般不用（`query_study_records` 已含拼写）。仅在用户要"看这个单词在墨墨里 ID 是什么"时用。

### Request

```
GET /vocabulary?spelling=apple
```

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `spelling` | string | ✅ | 单词拼写 |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "voc": {
      "id": "voc-iFfha6XNiyeiObQAgpqGrdziQsGlsDMt0TdbfVNUHYrQ4M3f55kO6OEkPGLeFp_c",
      "spelling": "apple"
    }
  },
  "success": true
}
```

**注意：只返回 `id` 和 `spelling`，没有释义/学习状态。** 释义走 `GET /interpretations?voc_id=...`，学习状态走 `query_study_records`。

---

## POST /vocabulary/query

**用途：** 批量查单词（按 spellings 或 ids 列表）。memo-context 写词前**确认 voc_id 用**。

### Request

```json
{
  "spellings": ["apple", "banana", "cherry"],
  "ids": ["voc-..."]
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `spellings` | string[] | ❌ | 拼写列表，**最多 1000** |
| `ids` | string[] | ❌ | ID 列表，**最多 1000** |

**⚠️ spellings 和 ids 不能同时用** — schema 提示"忽略其他条件"，实际是二选一。

### Response (200)

```json
{
  "errors": [],
  "data": {
    "voc": [
      {"id": "voc-...", "spelling": "apple"},
      {"id": "voc-...", "spelling": "banana"},
      {"id": "voc-...", "spelling": "cherry"}
    ]
  },
  "success": true
}
```

### 真实样例（2026-08-03 验证）

```python
import requests

# 批量查 3 个拼写
r = requests.post(
    f"{BASE}/vocabulary/query",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"spellings": ["apple", "banana", "cherry"]},
)
voc_list = r.json()["data"]["voc"]
# → [{id: voc-..., spelling: apple}, {id: voc-..., spelling: banana}, ...]
```

### 写词流程（memo-context 用法）

往云词本灌词时，**voc_id 是可选的**（云词本只接受 `content` 字符串，一行一词），但如果需要给单个词附加释义/例句/助记，**必须先拿到 voc_id**：

```python
# Step 1: 批量查 voc_id
r = requests.post(f"{BASE}/vocabulary/query",
    json={"spellings": ["apple", "banana"]})
voc_map = {v["spelling"]: v["id"] for v in r.json()["data"]["voc"]}

# Step 2: 给每个词创建释义
for spelling, voc_id in voc_map.items():
    requests.post(f"{BASE}/interpretations",
        json={"interpretation": {
            "voc_id": voc_id,
            "interpretation": f"自定义释义: {spelling}",
            "tags": [],
            "status": "PUBLISHED"
        }})
```
