# 例句

> 例句 CRUD。每个单词可以有多条例句。

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/phrases?voc_id=...](#get-phrases) | GET | 查某词的所有例句 | 🔶 备用 |
| [/phrases](#post-phrases) | POST | 创建例句 | 🔶 备用 |
| [/phrases/{id}](#post-phrasesid) | POST | 更新例句 | 🔶 备用 |
| [/phrases/{id}](#delete-phrasesid) | DELETE | 删除例句 | 🔶 备用 |

---

## 通用字段

### `Phrase` 对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 仅返回 | 例句 ID |
| `voc_id` | string | ✅（创建）| 单词 ID |
| `phrase` | string | ✅ | 例句英文，如 `"This is an apple."` |
| `interpretation` | string | ✅ | 翻译，如 `"这是一个苹果。"` |
| `tags` | string[] | ✅ | 标签（同样受"用户已用或预置"限制）|
| `origin` | string | ✅ | 来源，如 `"考研"`、`"原创"` |
| `highlight` | {start, end}[] | 仅返回 | 单词在例句中的高亮区间（`[start, end)`）|
| `status` | enum | 仅返回 | `PUBLISHED` / `DELETED` |
| `created_time` | ISO 8601 | 仅返回 | |
| `updated_time` | ISO 8601 | 仅返回 | |

### `status` 枚举

| 值 | 含义 |
|---|---|
| `PUBLISHED` | 发布 |
| `DELETED` | 删除（软删）|

---

## GET /phrases

### Request

```
GET /phrases?voc_id=voc-...
```

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `voc_id` | string | ✅ | 单词 ID |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "phrases": [
      {
        "id": "ph-...",
        "phrase": "This is an apple.",
        "interpretation": "这是一个苹果。",
        "tags": ["考研"],
        "highlight": [{"start": 10, "end": 15}],
        "status": "PUBLISHED",
        "created_time": "...",
        "updated_time": "...",
        "origin": "考研"
      }
    ]
  },
  "success": true
}
```

---

## POST /phrases

### Request

```json
{
  "phrase": {
    "voc_id": "voc-...",
    "phrase": "This is an apple.",
    "interpretation": "这是一个苹果。",
    "tags": ["考研"],
    "origin": "考研"
  }
}
```

### Response (200)

返回完整 `phrase` 对象（含 id 和 highlight）。

---

## POST /phrases/{id}

### Request

```json
{
  "phrase": {
    "phrase": "This is a red apple.",
    "interpretation": "这是一个红苹果。",
    "tags": ["考研"],
    "origin": "考研"
  },
  "id": "ph-..."
}
```

**注意：** 更新时 `voc_id` 不需要（绑死）。

---

## DELETE /phrases/{id}

### Request

```
DELETE /phrases/ph-...
```

### Response (200)

```json
{
  "errors": [],
  "data": {
    "phrase": { /* 软删后的对象，status: "DELETED" */ }
  },
  "success": true
}
```

**软删：** 不会从 GET 列表中消失，状态变成 `DELETED`。
