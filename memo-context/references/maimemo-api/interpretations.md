# 释义

> 自定义释义 CRUD。**用户为每个词维护自己的释义列表**。

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/interpretations?voc_id=...](#get-interpretations) | GET | 查某词的所有释义 | 🔶 备用 |
| [/interpretations](#post-interpretations) | POST | 创建释义 | 🔶 备用 |
| [/interpretations/{id}](#post-interpretationsid) | POST | 更新释义 | 🔶 备用 |
| [/interpretations/{id}](#delete-interpretationsid) | DELETE | 删除释义 | 🔶 备用 |

---

## 通用字段

### `Interpretation` 对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 仅返回 | 释义 ID |
| `voc_id` | string | ✅ | 单词 ID（从 `vocabulary/query` 拿）|
| `interpretation` | string | ✅ | 释义内容，如 `"n. 苹果"` |
| `tags` | string[] | ✅ | 标签数组（**必须是用户已用过的或墨墨预置**）|
| `status` | enum | ✅ | `PUBLISHED` / `UNPUBLISHED` / `DELETED` |
| `created_time` | ISO 8601 | 仅返回 | |
| `updated_time` | ISO 8601 | 仅返回 | |

### `status` 枚举

| 值 | 含义 |
|---|---|
| `PUBLISHED` | 发布 |
| `UNPUBLISHED` | 未发布 |
| `DELETED` | 删除（标记，不物理删除）|

### `tags` 限制

⚠️ **每个 tag 有最大创建数量限制** — 用户的"考研"和"GRE" tag 触发了 `interpretation_create_limitation` 错误。常见可行 tag：`默认`、`原创`、墨墨预置的（`CET4`、`TOEFL` 等）。**先 GET 看用户现有 tag，再复用**。

---

## GET /interpretations

**用途：** 查某单词的所有释义。

### Request

```
GET /interpretations?voc_id=voc-...
```

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `voc_id` | string | ✅ | 单词 ID |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "interpretations": [
      {
        "id": "intp-...",
        "interpretation": "n. 苹果",
        "tags": ["默认"],
        "status": "PUBLISHED",
        "created_time": "2026-08-03T14:30:14.934Z",
        "updated_time": "2026-08-03T14:30:14.934Z"
      }
    ]
  },
  "success": true
}
```

---

## POST /interpretations

**用途：** 创建释义。

### Request

```json
{
  "interpretation": {
    "voc_id": "voc-...",
    "interpretation": "n. 苹果",
    "tags": ["默认"],
    "status": "PUBLISHED"
  }
}
```

### Response (201)

```json
{
  "errors": [],
  "data": {
    "interpretation": {
      "id": "intp-...",
      "interpretation": "n. 苹果",
      "tags": ["默认"],
      "status": "PUBLISHED",
      "created_time": "...",
      "updated_time": "..."
    }
  },
  "success": true
}
```

### 错误

| 错误码 | 含义 | 怎么办 |
|---|---|---|
| `interpretation_invalid_tag` | tag 不在允许列表 | 查 GET 看用户现有 tag，留空 `[]`，或用预置 tag |
| `interpretation_create_limitation` | tag 达到最大创建数 | 换 tag 或编辑已有释义 |
| `common_invalid_param` | 缺必填字段 | 看 `info` 字段（会告诉你缺哪个）|

### 真实样例

```python
import requests

# 1) 查 voc_id
r = requests.post(f"{BASE}/vocabulary/query",
    json={"spellings": ["apple"]})
voc_id = r.json()["data"]["voc"][0]["id"]

# 2) 创建释义
r = requests.post(f"{BASE}/interpretations",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"interpretation": {
        "voc_id": voc_id,
        "interpretation": "n. 苹果；v. 吃",
        "tags": [],
        "status": "PUBLISHED"
    }})
new_id = r.json()["data"]["interpretation"]["id"]
```

---

## POST /interpretations/{id}

**用途：** 更新释义。

### Request

```json
{
  "interpretation": {
    "interpretation": "n. 苹果（修订）",
    "tags": ["默认"],
    "status": "PUBLISHED"
  },
  "id": "intp-..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | ✅ | 释义 ID（**顶层必须有**，跟 path 里的 id 一致）|
| `interpretation.interpretation` | string | ✅ | 新释义内容 |
| `interpretation.tags` | string[] | ✅ | 新标签 |
| `interpretation.status` | enum | ✅ | 新状态 |

**注意：** `voc_id` 在更新时**不能改**（schema 验证缺失，但语义上绑死了单词）。

### Response

同 POST 创建（返回更新后的 interpretation）。

---

## DELETE /interpretations/{id}

**用途：** 删除释义（**实际上是软删**，状态变成 `DELETED`）。

### Request

```
DELETE /interpretations/intp-...
```

### Response (200)

```json
{"errors": [], "data": {}, "success": true}
```

**注意：** 再次 GET 仍能看到该 interpretation（`status: DELETED`），不会从数组中消失。
